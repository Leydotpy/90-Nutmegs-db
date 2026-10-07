from unittest import mock

from apps.media.offline.models import Packaging
from apps.media.offline.tasks import (
    build_offline_package_streaming,
    build_offline_package_task,
)
from apps.posts.podcasts.models import Episode, Podcast
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from apps.media.offline.webhook import send_signed_webhook, validate_callback_url


@override_settings(
    DEBUG=False,
    OFFLINE_WEBHOOK_ALLOWED_ORIGINS=("https://hooks.example.test",),
)
class OfflineWebhookSecurityTests(SimpleTestCase):
    def test_configured_https_origin_allows_paths(self):
        callback = "https://hooks.example.test/offline/ready?job=1"

        self.assertEqual(validate_callback_url(callback), callback)

    @mock.patch("apps.media.offline.webhook.requests.post")
    def test_unlisted_private_origin_is_rejected_before_network_io(self, post):
        with self.assertRaisesMessage(
            ValidationError,
            "Offline callback origin is not allowed.",
        ):
            send_signed_webhook(
                "https://169.254.169.254/latest/meta-data/",
                {"status": "ready"},
                "test-secret",
            )

        post.assert_not_called()

    @mock.patch("apps.media.offline.webhook.requests.post")
    def test_configured_callback_is_signed_and_bounded(self, post):
        post.return_value.status_code = 204
        post.return_value.text = ""

        result = send_signed_webhook(
            "https://hooks.example.test/offline/ready",
            {"status": "ready"},
            "test-secret",
            timeout=3,
        )

        self.assertEqual(result, (204, ""))
        post.assert_called_once()
        call = post.call_args
        self.assertEqual(call.kwargs["timeout"], 3)
        self.assertFalse(call.kwargs["allow_redirects"])
        self.assertIn("X-Signature", call.kwargs["headers"])


class OfflineWorkerSafetyTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            username="offline-worker-listener",
            clerk_user_id="clerk_offline_worker_listener",
        )
        podcast = Podcast.objects.create(
            title="Offline worker safety",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        self.episode = Episode.objects.create(
            podcast=podcast,
            title="Protected worker download",
            public_release_date=timezone.now(),
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PUBLIC,
            premium_available_at=timezone.now(),
            public_available_at=timezone.now(),
        )

    @mock.patch("apps.media.offline.tasks.build_offline_package_streaming.__wrapped__")
    def test_disabled_job_is_failed_without_running_packager(self, packager):
        job = Packaging.objects.create(episode=self.episode, user=self.user)

        result = build_offline_package_task.run(str(job.pk))

        self.assertEqual(result, {"status": "disabled"})
        packager.assert_not_called()
        job.refresh_from_db()
        self.assertEqual(job.status, Packaging.STATUS_FAILED)
        self.assertEqual(job.error, "Offline packaging is disabled")

    def test_direct_streaming_task_is_disabled_before_creating_temp_files(self):
        with mock.patch("apps.media.offline.tasks.tempfile.mkdtemp") as make_temp:
            with self.assertRaisesMessage(RuntimeError, "Offline packaging is disabled"):
                build_offline_package_streaming.run(str(self.episode.pk), self.user.pk)

        make_temp.assert_not_called()
