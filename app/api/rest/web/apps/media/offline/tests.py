"""Safety tests for the deprecated custom offline DRM API."""

import uuid
from unittest import mock

from apps.media.offline.models import Device, Packaging
from apps.posts.podcasts.models import Episode, Podcast
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient


class OfflinePackagingSafetyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            username="offline-listener",
            clerk_user_id="clerk_offline_listener",
        )
        self.client.force_authenticate(self.user)
        podcast = Podcast.objects.create(
            title="Offline safety",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        self.episode = Episode.objects.create(
            podcast=podcast,
            title="Protected download",
            public_release_date=timezone.now(),
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PUBLIC,
            premium_available_at=timezone.now(),
            public_available_at=timezone.now(),
        )
        self.url = "/api/rest/web/apps/media/offline/packages/request/"
        self.payload = {
            "episode_id": str(self.episode.pk),
            "device_id": "device-1",
            "preset": "medium",
        }

    def test_device_registration_is_disabled_before_writing(self):
        response = self.client.post(
            "/api/rest/web/apps/media/offline/devices/register/",
            {
                "device_id": "device-1",
                "public_key_pem": "unused-while-disabled",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Device.objects.filter(user=self.user).exists())

    @override_settings(CUSTOM_OFFLINE_DRM_ENABLED=True)
    def test_device_registration_does_not_accept_server_managed_limit(self):
        device = Device.objects.create(
            user=self.user,
            device_id="device-1",
            public_key_pem="old-key",
            max_offline_items=3,
        )

        response = self.client.post(
            "/api/rest/web/apps/media/offline/devices/register/",
            {
                "device_id": "device-1",
                "public_key_pem": "new-key",
                "max_offline_items": 999,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        device.refresh_from_db()
        self.assertEqual(device.public_key_pem, "new-key")
        self.assertEqual(device.max_offline_items, 3)

    def test_packaging_status_is_disabled_before_lookup(self):
        response = self.client.get(
            f"/api/rest/web/apps/media/offline/packages/status/{uuid.uuid4()}/"
        )

        self.assertEqual(response.status_code, 403)

    @override_settings(CUSTOM_OFFLINE_DRM_ENABLED=True)
    def test_packaging_status_is_scoped_to_requesting_user(self):
        other_user = get_user_model().objects.create(
            username="other-offline-listener",
            clerk_user_id="clerk_other_offline_listener",
        )
        job = Packaging.objects.create(
            episode=self.episode,
            user=other_user,
            task_id="other-users-task",
        )

        response = self.client.get(
            f"/api/rest/web/apps/media/offline/packages/status/{job.task_id}/"
        )

        self.assertEqual(response.status_code, 404)

    @override_settings(CUSTOM_OFFLINE_DRM_ENABLED=True)
    def test_failed_packaging_status_does_not_expose_internal_error(self):
        job = Packaging.objects.create(
            episode=self.episode,
            user=self.user,
            task_id="failed-task",
            status=Packaging.STATUS_FAILED,
            error="secret provider response",
        )

        response = self.client.get(
            f"/api/rest/web/apps/media/offline/packages/status/{job.task_id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {"status": Packaging.STATUS_FAILED, "error": "Packaging failed"},
        )

    @mock.patch("api.rest.web.apps.media.offline.views.build_offline_package_task.apply_async")
    def test_custom_drm_is_disabled_by_default_before_any_job_is_created(self, enqueue):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, {"detail": "Offline packaging is not available."})
        enqueue.assert_not_called()

    @override_settings(CUSTOM_OFFLINE_DRM_ENABLED=True)
    @mock.patch("api.rest.web.apps.media.offline.views.build_offline_package_task.apply_async")
    def test_enabled_pipeline_uses_canonical_download_decision(self, enqueue):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["reason"], "requires_plan")
        enqueue.assert_not_called()

    @override_settings(CUSTOM_OFFLINE_DRM_ENABLED=True)
    def test_request_policy_fields_are_bounded(self):
        payload = {**self.payload, "days_valid": 31, "max_plays": 0}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("days_valid", response.data)
        self.assertIn("max_plays", response.data)
