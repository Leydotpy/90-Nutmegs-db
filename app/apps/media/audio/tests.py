# tests/test_process_audio.py
import datetime
import importlib
import os
from types import SimpleNamespace
from unittest import mock
from uuid import uuid4

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

# === UPDATE THIS to point at the module containing process_audio ===
MODULE_PATH = "apps.media.audio.tasks"  # <-- <--- change this to your real module path


class ProcessAudioTests(TestCase):
    def setUp(self):
        # Import target module once per test-run
        self.module = importlib.import_module(MODULE_PATH)

    def _make_dummy_audio(self, audio_id):
        """
        Create a dummy 'Audio' instance (not a full Django model) that matches
        the minimal API used by process_audio:
         - .id
         - .episode (with slug, pk, title, id)
         - .file with .chunks() generator yielding bytes
         - attributes updated by process_audio (name, bitrate, etc.)
         - .save(update_fields=...) method
         - .processed boolean
        """

        class DummyFile:
            def chunks(self):
                # small chunk sequence representing the stored file
                yield b"TEST-AUDIO-DATA"

        class DummyAudio:
            def __init__(self, _id):
                self.id = _id
                self.episode = SimpleNamespace(pk=42, slug="ep-slug", title="Episode Title", id=42)
                self.file = DummyFile()
                # fields that process_audio sets:
                self.name = None
                self.bitrate = None
                self.sample_rate = None
                self.codec = None
                self.duration = None
                self.processed = False

                # for file field behavior sometimes used by other helpers — not necessary here,
                # but keep attribute for compatibility.
                self.file_field = None

                # track save calls
                self._save_calls = []

            def save(self, update_fields=None):
                # record what fields were requested
                self._save_calls.append((update_fields or []))

        return DummyAudio(audio_id)

    def _capture_mkdtemp(self, created_list):
        """
        Return a side-effect function to patch tempfile.mkdtemp inside the module under test.
        It creates a unique directory with inherited permissions and appends its
        path to created_list for inspection.

        Python's tempfile.mkdtemp applies a private ACL on managed Windows test
        runners.  The sandbox can create that directory but cannot subsequently
        open files in or remove it, so use os.mkdir under this writable test
        package instead.  Production still exercises tempfile.mkdtemp; only its
        location-producing boundary is replaced here.
        """

        def mkdtemp_side_effect(*args, **kwargs):
            prefix = kwargs.get("prefix", "tmp")
            path = os.path.join(os.path.dirname(__file__), f"{prefix}{uuid4().hex}")
            os.mkdir(path)
            created_list.append(path)
            return path

        return mkdtemp_side_effect

    def test_process_audio_success_path_logs_and_cleans_tmpdir(self):
        module = self.module
        created_tmpdirs = []

        # Dummy audio instance and manager behavior
        audio_id = "success-1"
        dummy_audio = self._make_dummy_audio(audio_id=audio_id)

        # Setup mocks on module functions used by process_audio
        with mock.patch(f"{MODULE_PATH}.tempfile.mkdtemp", side_effect=self._capture_mkdtemp(created_tmpdirs)):
            with mock.patch(f"{MODULE_PATH}.Audio") as AudioMock:
                # Create DoesNotExist exception class on mock to match code's except
                AudioMock.DoesNotExist = type("DoesNotExist", (Exception,), {})

                # Configure manager chain .select_related(...).get(id=audio_id) -> dummy_audio
                select_related_ret = mock.MagicMock()
                select_related_ret.get.return_value = dummy_audio
                AudioMock.objects.select_related.return_value = select_related_ret

                # Patch heavy IO functions to be no-ops / deterministic:
                with mock.patch(f"{MODULE_PATH}.detect_master_audio_info", return_value={
                    "title": "Detected Title",
                    "bitrate_kbps": 128,
                    "sample_rate": 44100,
                    "codec": "mp3",
                    "duration": 60.0,
                }), \
                        mock.patch(f"{MODULE_PATH}.generate_variants", return_value=[]), \
                        mock.patch(f"{MODULE_PATH}.generate_hls_stream", return_value=None), \
                        mock.patch(f"{MODULE_PATH}.generate_preview_clip", return_value=None), \
                        mock.patch(f"{MODULE_PATH}.generate_transcription", return_value=None):
                    # Run and assert that the successful path emits no errors.
                    logger_name = module.__name__
                    with self.assertNoLogs(logger_name, level="ERROR"):
                        result = module.process_audio(audio_id=audio_id, user_id=None)

                    # Assertions: function returned audio.id and marked processed True
                    self.assertEqual(result, audio_id, "process_audio should return the audio id on success")
                    self.assertTrue(dummy_audio.processed, "Audio.processed should be True after processing")
                    # ensure save was called for processed flag at least once
                    self.assertTrue(any("processed" in (fields or []) for fields in dummy_audio._save_calls),
                                    f"Expected save(update_fields=['processed']) calls recorded; got {dummy_audio._save_calls}")

                    # ensure tempdir was created and then removed
                    # created_tmpdirs should have at least one path, and it must not exist now
                    self.assertTrue(len(created_tmpdirs) >= 1,
                                    f"Expected created tmpdirs captured, got {created_tmpdirs}")
                    for p in created_tmpdirs:
                        self.assertFalse(os.path.exists(p),
                                         f"Tempdir {p!r} should be removed after process_audio finishes")

    def test_process_audio_transcription_raises_is_logged_but_processing_continues(self):
        module = self.module
        created_tmpdirs = []
        audio_id = "transcribe-fail-1"
        dummy_audio = self._make_dummy_audio(audio_id=audio_id)

        with mock.patch(f"{MODULE_PATH}.tempfile.mkdtemp", side_effect=self._capture_mkdtemp(created_tmpdirs)):
            with mock.patch(f"{MODULE_PATH}.Audio") as AudioMock:
                AudioMock.DoesNotExist = type("DoesNotExist", (Exception,), {})
                select_related_ret = mock.MagicMock()
                select_related_ret.get.return_value = dummy_audio
                AudioMock.objects.select_related.return_value = select_related_ret

                # detection still succeeds
                with mock.patch(f"{MODULE_PATH}.detect_master_audio_info", return_value={
                    "title": "Detected Title",
                    "bitrate_kbps": 64,
                    "sample_rate": 22050,
                    "codec": "mp3",
                    "duration": 30.0,
                }), \
                        mock.patch(f"{MODULE_PATH}.generate_variants", return_value=[]), \
                        mock.patch(f"{MODULE_PATH}.generate_hls_stream", return_value=None), \
                        mock.patch(f"{MODULE_PATH}.generate_preview_clip", return_value=None), \
                        mock.patch(f"{MODULE_PATH}.generate_transcription",
                                   side_effect=RuntimeError("ASR provider crashed")):
                    # Because process_audio calls logger.exception on transcription failure,
                    # capture logs and assert that the exception was logged. The function should continue.
                    logger_name = module.__name__
                    with self.assertLogs(logger_name, level="ERROR") as log_cm:
                        result = module.process_audio(audio_id)

                    # The function should not raise but should return id and mark processed True
                    self.assertEqual(result, audio_id)
                    self.assertTrue(dummy_audio.processed,
                                    "Even with transcription failure, audio.processed should still be set")

                    # the last ERROR log should contain the message "Transcription generation failed"
                    error_logs = [entry for entry in log_cm.output if
                                  "Transcription generation failed" in entry or
                                  "Transcription provider failed" in entry]
                    self.assertTrue(error_logs, f"Expected transcription-related ERROR logs, got: {log_cm.output}")

                    # tmpdir should be cleaned up
                    for p in created_tmpdirs:
                        self.assertFalse(os.path.exists(p),
                                         f"Tempdir {p!r} should be removed after process_audio finishes")

    def test_process_audio_audio_not_found_returns_none_and_cleans_tmpdir(self):
        module = self.module
        created_tmpdirs = []
        audio_id = "missing-audio-1"

        with mock.patch(f"{MODULE_PATH}.tempfile.mkdtemp", side_effect=self._capture_mkdtemp(created_tmpdirs)):
            with mock.patch(f"{MODULE_PATH}.Audio") as AudioMock:
                # create DoesNotExist exception class
                AudioMock.DoesNotExist = type("DoesNotExist", (Exception,), {})

                # configure select_related(...).get to raise DoesNotExist
                select_related_ret = mock.MagicMock()
                select_related_ret.get.side_effect = AudioMock.DoesNotExist()
                AudioMock.objects.select_related.return_value = select_related_ret

                # Run
                result = module.process_audio(audio_id)

                # Should return None when audio not found
                self.assertIsNone(result, "process_audio should return None for nonexistent audio")

                # tmpdir created then removed
                self.assertTrue(len(created_tmpdirs) >= 1,
                                "Expected tempfile to be created even for missing audio case")
                for p in created_tmpdirs:
                    self.assertFalse(os.path.exists(p), f"Tempdir {p!r} should be removed even when audio missing")

    @mock.patch(f"{MODULE_PATH}.generate_cloudfront_signed_cookies")
    @mock.patch(f"{MODULE_PATH}.Audio")
    def test_cloudfront_rotation_caches_timezone_aware_expiry(
        self,
        audio_model,
        sign_cookies,
    ):
        hls_id = uuid4()
        audio_model.Quality.HLS = "hls"
        audio_model.objects.filter.return_value.values.return_value = [
            {
                "id": hls_id,
                "prefix": "episodes/test/hls",
                "file": "episodes/test/hls/index.m3u8",
            }
        ]
        expires_at = timezone.now() + datetime.timedelta(minutes=10)
        sign_cookies.return_value = {
            "cookies": {
                "CloudFront-Key-Pair-Id": "key",
                "CloudFront-Policy": "signed-policy",
                "CloudFront-Signature": "signed-signature",
            },
            "expires_at": expires_at,
        }
        cache_key = f"cf_signed_cookies:{hls_id}"
        cache.delete(cache_key)

        with mock.patch.object(self.module.settings, "CLOUDFRONT_DOMAIN", "media.example.test"), \
                mock.patch.object(self.module.settings, "CLOUDFRONT_COOKIE_DOMAIN", "example.test"), \
                mock.patch.object(self.module.settings, "CLOUDFRONT_KEY_PAIR_ID", "key"), \
                mock.patch.object(self.module.settings, "CLOUDFRONT_PRIVATE_KEY", "private"):
            self.module.rotate_cloud_front_cookies()

        cached = cache.get(cache_key)
        self.assertEqual(cached["expires_at"], expires_at)
        self.assertTrue(timezone.is_aware(cached["expires_at"]))
        self.assertEqual(
            cached["resource_url"],
            "https://media.example.test/episodes/test/hls/*",
        )
