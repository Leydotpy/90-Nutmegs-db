"""Tests for provider-neutral direct upload orchestration."""

from datetime import UTC, datetime
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.media.canonical import MediaAccessClass, MediaAsset
from apps.media.providers.contracts import UploadIntent
from apps.media.upload_intents import (
    UploadIntentRejected,
    UploadIntentRequest,
    UploadIntentService,
)


class UploadIntentServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="intent-owner",
            email="intent-owner@example.test",
            clerk_user_id="clerk-intent-owner",
        )
        self.asset = MediaAsset.objects.create(
            created_by=self.user,
            media_type=MediaAsset.MediaType.AUDIO,
            mime_type="audio/mpeg",
            byte_size=1024,
            original_filename="attacker controlled name.mp3",
        )
        self.private_objects = mock.Mock()
        self.images = mock.Mock()
        self.video = mock.Mock()
        self.service = UploadIntentService(
            private_object_storage=self.private_objects,
            image_platform=self.images,
            video_platform=self.video,
            max_upload_bytes=500_000_000,
            max_duration_seconds=7200,
            upload_ttl_seconds=600,
            stream_allowed_origins=("app.example.test",),
        )
        self.now = datetime(2026, 8, 28, 12, tzinfo=UTC)

    def request(self, **overrides):
        values = {
            "asset_id": self.asset.pk,
            "product": "r2",
        }
        values.update(overrides)
        return UploadIntentRequest(**values)

    def update_asset(self, **values):
        for field, value in values.items():
            setattr(self.asset, field, value)
        self.asset.save(update_fields=(*values.keys(), "updated_at"))

    def test_r2_key_is_opaque_and_does_not_use_raw_filename(self):
        self.private_objects.create_upload_intent.return_value = UploadIntent(
            provider="cloudflare",
            product="r2",
            resource_id="key",
            upload_url="https://upload/secret",
        )
        request = self.request()

        self.service.create(request, actor=self.user, now=self.now)

        call = self.private_objects.create_upload_intent.call_args.kwargs
        self.assertTrue(call["key"].startswith(f"temporary/uploads/{request.asset_id.hex}/"))
        self.assertTrue(call["key"].endswith(".mp3"))
        self.assertNotIn("attacker", call["key"])

    def test_oversize_request_is_rejected_before_provider_call(self):
        self.update_asset(byte_size=500_000_001)

        with self.assertRaises(UploadIntentRejected):
            self.service.create(self.request(), actor=self.user, now=self.now)

        self.private_objects.create_upload_intent.assert_not_called()
        self.images.create_upload_intent.assert_not_called()
        self.video.create_upload_intent.assert_not_called()

    def test_public_r2_upload_stages_only_in_the_private_bucket(self):
        self.update_asset(access_class=MediaAccessClass.PUBLIC)
        self.private_objects.create_upload_intent.return_value = UploadIntent(
            provider="cloudflare",
            product="r2",
            resource_id="key",
            upload_url="https://upload/secret",
        )

        self.service.create(self.request(), actor=self.user, now=self.now)

        self.private_objects.create_upload_intent.assert_called_once()

    def test_public_managed_media_still_requires_signed_delivery_during_ingest(self):
        self.update_asset(
            access_class=MediaAccessClass.PUBLIC,
            media_type=MediaAsset.MediaType.IMAGE,
            mime_type="image/jpeg",
            original_filename="cover.jpg",
        )
        self.images.create_upload_intent.return_value = UploadIntent(
            provider="cloudflare",
            product="images",
            resource_id="image-id",
            upload_url="https://upload/secret",
        )

        self.service.create(
            self.request(product="images"),
            actor=self.user,
            now=self.now,
        )

        self.assertTrue(self.images.create_upload_intent.call_args.kwargs["private"])

    def test_public_stream_still_requires_signed_delivery_during_ingest(self):
        self.update_asset(
            access_class=MediaAccessClass.PUBLIC,
            media_type=MediaAsset.MediaType.VIDEO,
            mime_type="video/mp4",
            original_filename="episode.mp4",
        )
        self.video.create_upload_intent.return_value = UploadIntent(
            provider="cloudflare",
            product="stream",
            resource_id="video-id",
            upload_url="https://upload/secret",
        )

        self.service.create(
            self.request(product="stream"),
            actor=self.user,
            now=self.now,
        )

        self.assertTrue(self.video.create_upload_intent.call_args.kwargs["private"])

    def test_private_image_metadata_includes_canonical_asset_id(self):
        self.update_asset(
            media_type=MediaAsset.MediaType.IMAGE,
            mime_type="image/jpeg",
            original_filename="cover.jpg",
        )
        self.images.create_upload_intent.return_value = UploadIntent(
            provider="cloudflare",
            product="images",
            resource_id="image-id",
            upload_url="https://upload/secret",
        )
        request = self.request(product="images")

        self.service.create(request, actor=self.user, now=self.now)

        call = self.images.create_upload_intent.call_args.kwargs
        self.assertTrue(call["private"])
        self.assertEqual(call["metadata"]["sanfootball_asset_id"], str(request.asset_id))

    def test_video_duration_limit_is_rejected_before_provider_call(self):
        self.update_asset(
            media_type=MediaAsset.MediaType.VIDEO,
            mime_type="video/mp4",
            original_filename="source.mp4",
        )
        request = self.request(product="stream", max_duration_seconds=7201)

        with self.assertRaisesMessage(UploadIntentRejected, "duration"):
            self.service.create(request, actor=self.user, now=self.now)

        self.video.create_upload_intent.assert_not_called()

    def test_non_positive_video_duration_is_rejected_before_provider_call(self):
        self.update_asset(
            media_type=MediaAsset.MediaType.VIDEO,
            mime_type="video/mp4",
            original_filename="source.mp4",
        )
        for duration in (0, -1):
            with (
                self.subTest(duration=duration),
                self.assertRaisesMessage(UploadIntentRejected, "positive"),
            ):
                self.service.create(
                    self.request(
                        product="stream",
                        max_duration_seconds=duration,
                    ),
                    actor=self.user,
                    now=self.now,
                )

        self.video.create_upload_intent.assert_not_called()

    def test_foreign_actor_is_rejected_before_provider_call(self):
        other_user = get_user_model().objects.create_user(
            username="not-the-intent-owner",
            email="not-owner@example.test",
            clerk_user_id="clerk-not-intent-owner",
        )

        with self.assertRaisesMessage(UploadIntentRejected, "not available"):
            self.service.create(self.request(), actor=other_user, now=self.now)

        self.private_objects.create_upload_intent.assert_not_called()
        self.images.create_upload_intent.assert_not_called()
        self.video.create_upload_intent.assert_not_called()

    def test_non_pending_asset_is_rejected_before_provider_call(self):
        self.update_asset(status=MediaAsset.Status.READY)

        with self.assertRaisesMessage(UploadIntentRejected, "not pending"):
            self.service.create(self.request(), actor=self.user, now=self.now)

        self.private_objects.create_upload_intent.assert_not_called()
        self.images.create_upload_intent.assert_not_called()
        self.video.create_upload_intent.assert_not_called()

    def test_failed_asset_can_request_a_fresh_private_upload_capability(self):
        self.update_asset(status=MediaAsset.Status.FAILED)
        self.private_objects.create_upload_intent.return_value = UploadIntent(
            provider="cloudflare",
            product="r2",
            resource_id="retry-key",
            upload_url="https://upload/secret",
        )

        self.service.create(self.request(), actor=self.user, now=self.now)

        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, MediaAsset.Status.PENDING_UPLOAD)
        self.private_objects.create_upload_intent.assert_called_once()

    def test_client_declared_checksum_is_rejected_before_provider_call(self):
        self.update_asset(checksum="a" * 64)

        with self.assertRaisesMessage(UploadIntentRejected, "trusted processing"):
            self.service.create(self.request(), actor=self.user, now=self.now)

        self.private_objects.create_upload_intent.assert_not_called()
        self.images.create_upload_intent.assert_not_called()
        self.video.create_upload_intent.assert_not_called()

    def test_product_must_match_canonical_media_type(self):
        with self.assertRaisesMessage(UploadIntentRejected, "video asset"):
            self.service.create(
                self.request(product="stream"),
                actor=self.user,
                now=self.now,
            )

        self.private_objects.create_upload_intent.assert_not_called()
        self.images.create_upload_intent.assert_not_called()
        self.video.create_upload_intent.assert_not_called()
