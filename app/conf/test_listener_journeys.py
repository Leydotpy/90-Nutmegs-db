"""Supported listener journeys through real routes, serializers and domain owners.

Signing is replaced only at the external storage boundary. These tests deliberately
do not present anonymous queue mutation, login merge or the legacy follow HTTP
endpoint as working; their observed gaps belong in the implementation ledger.
"""

import datetime
from unittest import mock

from apps.media.audio.models import Audio
from apps.memberships.access import AccessService
from apps.memberships.models import Entitlement, Plan, Subscription
from apps.posts.podcasts.models import Episode, PlayBack, Podcast
from apps.queue.models import AppLabel, Queue
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

SIGNING_BOUNDARY = "api.rest.web.apps.media.streaming.views.generate_presigned_url_for_name"
API_ROOT = "/api/rest/web/apps"


class ListenerJourneyTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        AccessService._instance = None
        self.addCleanup(setattr, AccessService, "_instance", None)
        self.client = APIClient()
        self.published_at = timezone.now() - datetime.timedelta(hours=1)
        self.podcast = Podcast.objects.create(
            title="Listener journeys",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=self.published_at,
        )
        self.plan = Plan.objects.create(name="Journey fan", tier=Plan.Level.FAN)

    def user(self, name):
        return get_user_model().objects.create_user(
            username=name,
            email=f"{name}@example.test",
            clerk_user_id=f"clerk-{name}",
            password="test-password",
        )

    def episode(self, title, *, premium=False, preview=False):
        episode = Episode.objects.create(
            podcast=self.podcast,
            title=title,
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PLAN if premium else Episode.Visibility.PUBLIC,
            published_at=self.published_at,
            premium_available_at=self.published_at,
            public_available_at=None if premium else self.published_at,
            required_plan=self.plan if premium else None,
            exclusive=premium,
        )
        Audio.objects.create(
            episode=episode,
            name=f"{title} master",
            quality=Audio.Quality.MEDIUM,
            file=f"episodes/{episode.pk}/master.mp3",
            duration=3600,
            master=True,
            processed=True,
        )
        if preview:
            Audio.objects.create(
                episode=episode,
                name=f"{title} preview",
                quality=Audio.Quality.PREVIEW,
                file=f"episodes/{episode.pk}/preview.mp3",
                duration=30,
                processed=True,
            )
        return episode

    @staticmethod
    def detail_url(episode):
        return f"{API_ROOT}/podcast/episode/{episode.slug}/"

    @staticmethod
    def stream_url(episode):
        return f"{API_ROOT}/media/streaming/episodes/{episode.pk}/stream/"

    @mock.patch(SIGNING_BOUNDARY, return_value="https://cdn.example.test/public?signature=test")
    def test_anonymous_listener_discovers_public_episode_and_plays_full_audio(self, sign_url):
        episode = self.episode("Public match review")

        show = self.client.get(f"{API_ROOT}/podcast/{self.podcast.slug}/")
        self.assertEqual(show.status_code, 200, show.data)
        self.assertEqual([row["id"] for row in show.data["episodes"]["results"]], [str(episode.pk)])
        metadata = self.client.get(self.detail_url(episode))
        self.assertEqual(metadata.status_code, 200, metadata.data)
        self.assertTrue(metadata.data["user_has_access"])
        self.assertNotIn("url", metadata.data)

        stream = self.client.get(self.stream_url(episode))
        self.assertEqual(stream.status_code, 200, stream.data)
        self.assertEqual(
            stream.data,
            {
                "url": sign_url.return_value,
                "type": "full",
                "quality": Audio.Quality.MEDIUM,
            },
        )
        self.assertEqual(sign_url.call_args.args[1], f"episodes/{episode.pk}/master.mp3")
        self.assertEqual(sign_url.call_args.kwargs["expires_in"], settings.PRESIGN_EXPIRES_SECONDS)
        self.assertTrue(sign_url.call_args.kwargs["allow_public"])
        self.assertFalse(stream.cookies)

    @mock.patch(SIGNING_BOUNDARY, return_value="https://cdn.example.test/preview?signature=test")
    def test_anonymous_premium_discovery_issues_only_preview_and_denies_hls(self, sign_url):
        episode = self.episode("Premium analysis", premium=True, preview=True)

        metadata = self.client.get(self.detail_url(episode))
        self.assertEqual(metadata.status_code, 200, metadata.data)
        self.assertFalse(metadata.data["user_has_access"])
        self.assertFalse(metadata.data["downloadable"])
        self.assertNotIn("url", metadata.data)

        preview = self.client.get(self.stream_url(episode))
        self.assertEqual(preview.status_code, 200, preview.data)
        self.assertEqual(preview.data, {"url": sign_url.return_value, "type": "preview"})
        sign_url.assert_called_once()
        self.assertEqual(sign_url.call_args.args[1], f"episodes/{episode.pk}/preview.mp3")
        self.assertEqual(
            sign_url.call_args.kwargs["expires_in"], settings.PRESIGN_PREVIEW_EXPIRES_SECONDS
        )
        self.assertFalse(sign_url.call_args.kwargs["allow_public"])

        hls = self.client.get(self.stream_url(episode), {"format": "hls"})
        self.assertEqual(hls.status_code, 403, hls.data)
        self.assertEqual(hls.data["reason"], "requires_login")
        self.assertNotIn("url", hls.data)
        self.assertNotIn("playlist_url", hls.data)
        self.assertFalse(hls.cookies)
        sign_url.assert_called_once()

    def test_authenticated_queue_add_read_remove_clear_and_owner_isolation(self):
        owner = self.user("queue-owner")
        other = self.user("other-queue-owner")
        first = self.episode("First queued episode")
        second = self.episode("Second queued episode")
        self.client.force_authenticate(user=owner)

        for episode in (first, second, first):
            response = self.client.post(
                f"{API_ROOT}/queue/add/",
                {"item_id": str(episode.pk), "app_label": AppLabel.EPISODE},
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.data)
        queue = Queue.objects.get(owner=owner)
        self.assertEqual(queue.items.count(), 2)
        listed = self.client.get(f"{API_ROOT}/queue/")
        self.assertEqual(listed.status_code, 200, listed.data)
        self.assertEqual(
            [row["track"]["id"] for row in listed.data["tracks"]],
            [str(first.pk), str(second.pk)],
        )

        self.client.force_authenticate(user=other)
        other_queue = self.client.get(f"{API_ROOT}/queue/")
        self.assertEqual(other_queue.status_code, 200, other_queue.data)
        self.assertEqual(other_queue.data["tracks"], [])
        removed_by_other = self.client.delete(f"{API_ROOT}/queue/{first.pk}/remove/")
        self.assertEqual(removed_by_other.status_code, 200, removed_by_other.data)
        self.assertTrue(queue.items.filter(track=first).exists())

        self.client.force_authenticate(user=owner)
        removed = self.client.delete(f"{API_ROOT}/queue/{first.pk}/remove/")
        self.assertEqual(removed.status_code, 200, removed.data)
        self.assertEqual(removed.data, {"deleted": 1})
        cleared = self.client.put(f"{API_ROOT}/queue/clear/", {}, format="json")
        self.assertEqual(cleared.status_code, 200, cleared.data)
        self.assertFalse(queue.items.exists())
        self.assertEqual(self.client.get(f"{API_ROOT}/queue/").data["tracks"], [])

    def test_progress_checkpoint_resumes_only_for_owner_and_completion_removes_it(self):
        owner = self.user("progress-owner")
        other = self.user("other-progress-owner")
        episode = self.episode("One hour match analysis")
        checkpoint_url = f"{API_ROOT}/podcast/episode/{episode.slug}/update-playback"
        resume_url = f"{API_ROOT}/podcast/resume-playback/"
        self.client.force_authenticate(user=owner)

        checkpoint = self.client.patch(
            checkpoint_url, {"seconds": 1200, "is_completed": False}, format="json"
        )
        self.assertEqual(checkpoint.status_code, 200, checkpoint.data)
        self.assertEqual(checkpoint.data["seconds"], 1200)
        playback = PlayBack.objects.get(user=owner, episode=episode)
        self.assertFalse(playback.is_completed)
        resume = self.client.get(resume_url)
        self.assertEqual(resume.status_code, 200, resume.data)
        self.assertEqual(len(resume.data["results"]), 1)
        self.assertEqual(resume.data["results"][0]["episode"]["id"], str(episode.pk))
        self.assertEqual(resume.data["results"][0]["current_timestamp"], 1200)

        self.client.force_authenticate(user=other)
        other_history = self.client.get(resume_url)
        self.assertEqual(other_history.status_code, 200, other_history.data)
        self.assertEqual(other_history.data["results"], [])

        self.client.force_authenticate(user=owner)
        completed = self.client.patch(
            checkpoint_url, {"seconds": 3600, "is_completed": True}, format="json"
        )
        self.assertEqual(completed.status_code, 200, completed.data)
        playback.refresh_from_db()
        self.assertTrue(playback.is_completed)
        self.assertEqual(PlayBack.objects.filter(user=owner, episode=episode).count(), 1)
        self.assertEqual(self.client.get(resume_url).data["results"], [])

    @mock.patch(SIGNING_BOUNDARY)
    def test_existing_free_follow_owner_does_not_grant_paid_stream_access(self, sign_url):
        listener = self.user("free-follower")
        episode = self.episode("Members only", premium=True)
        # Exercise the existing follow owner directly: the legacy follow HTTP
        # response and library selector are deferred defects, not contracts.
        self.assertTrue(self.podcast.toggle_subscription(listener))
        self.client.force_authenticate(user=listener)

        metadata = self.client.get(self.detail_url(episode))
        self.assertEqual(metadata.status_code, 200, metadata.data)
        self.assertTrue(metadata.data["user_has_subscribed"])
        self.assertFalse(metadata.data["user_has_access"])
        self.assertFalse(metadata.data["downloadable"])
        stream = self.client.get(self.stream_url(episode))
        self.assertEqual(stream.status_code, 403, stream.data)
        self.assertNotIn("url", stream.data)
        self.assertFalse(Subscription.objects.filter(membership__user=listener).exists())
        self.assertFalse(Entitlement.objects.filter(user=listener).exists())
        sign_url.assert_not_called()
