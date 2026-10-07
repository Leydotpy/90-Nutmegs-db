import datetime
from types import SimpleNamespace

from api.rest.web.apps.queue.views import QueueViewSet
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.media.models import PlayList
from apps.posts.podcasts.models import Episode, Podcast
from apps.queue.models import AppLabel, Queue
from apps.queue.signals import merge_anon_queue_to_user
from apps.queue.utils import get_or_create_queue_for_request


class _TestSession:
    """Small request-session boundary used by queue ownership tests."""

    def __init__(self, session_key=None):
        self.session_key = session_key

    def save(self):
        self.session_key = self.session_key or "test-anonymous-session"


class QueueOwnershipTests(TestCase):
    @staticmethod
    def create_user(username):
        return get_user_model().objects.create(
            username=username,
            clerk_user_id=f"clerk_{username}",
        )

    def test_authenticated_request_creates_and_reuses_owner_queue(self):
        user = self.create_user("owner")
        request = SimpleNamespace(user=user, session=_TestSession())

        first = get_or_create_queue_for_request(request)
        second = get_or_create_queue_for_request(request)

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.owner, user)
        self.assertIsNone(first.session_key)
        self.assertEqual(Queue.objects.filter(owner=user).count(), 1)

    def test_anonymous_request_creates_session_and_reuses_its_queue(self):
        request = SimpleNamespace(user=AnonymousUser(), session=_TestSession())

        first = get_or_create_queue_for_request(request)
        second = get_or_create_queue_for_request(request)

        self.assertEqual(first.pk, second.pk)
        self.assertTrue(first.is_anonymous())
        self.assertEqual(first.session_key, "test-anonymous-session")
        self.assertEqual(
            Queue.objects.filter(session_key="test-anonymous-session").count(),
            1,
        )

    def test_open_manager_uses_merge_timestamp_as_lifecycle_state(self):
        open_queue, created = Queue.open.get_or_create(session_key="still-open")
        Queue.objects.create(
            session_key="already-merged",
            date_merged=timezone.now(),
        )

        self.assertTrue(created)
        self.assertEqual(list(Queue.open.all()), [open_queue])
        self.assertEqual(
            list(Queue.objects.merged().values_list("session_key", flat=True)),
            ["already-merged"],
        )


class QueueItemBehaviorTests(TestCase):
    def setUp(self):
        self.podcast = Podcast.objects.create(
            title="Queue test podcast",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        self.queue = Queue.objects.create(session_key="queue-item-session")

    def create_episode(self, title):
        return Episode.objects.create(
            podcast=self.podcast,
            title=title,
            status=Episode.PublicationStatus.PUBLISHED,
        )

    def add_episode(self, episode, *, override=False):
        self.queue.add_item(
            item_id=str(episode.pk),
            app_label=AppLabel.EPISODE,
            override=override,
        )

    def test_add_episode_is_idempotent(self):
        episode = self.create_episode("Only once")

        self.add_episode(episode)
        self.add_episode(episode)

        self.assertEqual(self.queue.items.count(), 1)
        self.assertEqual(self.queue.items.get().track, episode)

    def test_position_is_the_runtime_order_for_append_and_prepend(self):
        first = self.create_episode("First")
        second = self.create_episode("Second")
        prepended = self.create_episode("Prepended")

        self.add_episode(first)
        # Evaluate the compatibility property before another insertion. This
        # protects against returning a stale cached queryset after add_item().
        self.assertEqual(
            [item.track_id for item in self.queue.tracks],
            [first.pk],
        )
        self.add_episode(second)
        self.add_episode(prepended, override=True)

        self.assertEqual(
            [item.track_id for item in self.queue.tracks],
            [prepended.pk, first.pk, second.pk],
        )
        self.assertEqual(
            list(
                self.queue.items.order_by("position", "added_at", "pk").values_list(
                    "position", flat=True
                )
            ),
            [0, 1, 2],
        )

    def test_podcast_expansion_excludes_unpublished_episodes(self):
        published = self.create_episode("Published")
        Episode.objects.create(
            podcast=self.podcast,
            title="Draft",
            status=Episode.PublicationStatus.DRAFT,
        )
        Episode.objects.create(
            podcast=self.podcast,
            title="Archived",
            status=Episode.PublicationStatus.ARCHIVED,
        )

        self.queue.add_item(str(self.podcast.pk), AppLabel.PODCAST)

        self.assertEqual(
            list(self.queue.items.values_list("track_id", flat=True)),
            [published.pk],
        )

    def test_direct_unpublished_episode_is_rejected(self):
        draft = Episode.objects.create(
            podcast=self.podcast,
            title="Draft",
            status=Episode.PublicationStatus.DRAFT,
        )

        with self.assertRaisesRegex(ValueError, "not available"):
            self.add_episode(draft)

        self.assertFalse(self.queue.items.exists())

    def test_direct_episode_under_unpublished_or_legacy_child_show_is_rejected(self):
        draft = Podcast.objects.create(title="Draft queue owner")
        future = Podcast.objects.create(
            title="Future queue owner",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now() + datetime.timedelta(days=1),
        )
        parent = Podcast.objects.create(
            title="Queue legacy parent",
            structure=Podcast.Structure.PARENT,
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        child = Podcast.objects.create(
            title="Queue legacy child",
            structure=Podcast.Structure.CHILD,
            parent=parent,
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        episodes = [
            Episode.objects.create(
                podcast=podcast,
                title=f"Hidden queue episode {index}",
                status=Episode.PublicationStatus.PUBLISHED,
            )
            for index, podcast in enumerate((draft, future, child), start=1)
        ]

        for episode in episodes:
            with self.assertRaisesRegex(ValueError, "not available"):
                self.add_episode(episode)

        self.assertFalse(self.queue.items.exists())

    def test_saved_queue_item_disappears_when_owning_podcast_is_unpublished(self):
        episode = self.create_episode("Owner is later unpublished")
        self.add_episode(episode)
        self.podcast.status = Podcast.PublicationStatus.DRAFT
        self.podcast.published_at = None
        self.podcast.save(update_fields=("status", "published_at", "updated"))

        self.assertEqual(list(self.queue.tracks), [])
        self.assertTrue(self.queue.items.filter(track=episode).exists())

    def test_private_playlist_cannot_be_expanded_by_another_queue_owner(self):
        playlist_owner = get_user_model().objects.create(
            username="private-playlist-owner",
            clerk_user_id="clerk_private_playlist_owner",
        )
        queue_owner = get_user_model().objects.create(
            username="private-playlist-intruder",
            clerk_user_id="clerk_private_playlist_intruder",
        )
        playlist = PlayList.objects.create(name="Private playlist", user=playlist_owner)
        playlist.items.add(self.create_episode("Private playlist episode"))
        queue = Queue.objects.create(owner=queue_owner)

        with self.assertRaisesRegex(ValueError, "not available"):
            queue.add_item(str(playlist.pk), AppLabel.PLAYLIST)

        self.assertFalse(queue.items.exists())


class QueueLoginMergeTests(TestCase):
    @staticmethod
    def create_user(username):
        return get_user_model().objects.create(
            username=username,
            clerk_user_id=f"clerk_{username}",
        )

    def test_login_merge_moves_in_order_skips_duplicates_and_deletes_source(self):
        user = self.create_user("listener")
        podcast = Podcast.objects.create(
            title="Merge test podcast",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        existing = Episode.objects.create(
            podcast=podcast,
            title="Existing",
            status=Episode.PublicationStatus.PUBLISHED,
        )
        anonymous_only = Episode.objects.create(
            podcast=podcast,
            title="Anonymous only",
            status=Episode.PublicationStatus.PUBLISHED,
        )
        user_queue = Queue.objects.create(owner=user)
        anonymous_queue = Queue.objects.create(session_key="anon-before-login")

        user_queue.add_item(str(existing.pk), AppLabel.EPISODE)
        anonymous_queue.add_item(str(existing.pk), AppLabel.EPISODE)
        anonymous_queue.add_item(str(anonymous_only.pk), AppLabel.EPISODE)

        request = SimpleNamespace(
            session=SimpleNamespace(session_key="anon-before-login"),
        )
        merge_anon_queue_to_user(sender=None, user=user, request=request)

        user_queue.refresh_from_db()
        self.assertEqual(
            list(
                user_queue.items.order_by("position", "added_at", "pk").values_list(
                    "track_id", flat=True
                )
            ),
            [existing.pk, anonymous_only.pk],
        )
        self.assertEqual(user_queue.items.count(), 2)
        self.assertFalse(Queue.objects.filter(pk=anonymous_queue.pk).exists())


class QueueAPIContractTests(TestCase):
    def test_remove_route_accepts_episode_uuid_and_deletes_by_track(self):
        user = get_user_model().objects.create(
            username="api-listener",
            clerk_user_id="clerk_api_listener",
        )
        podcast = Podcast.objects.create(
            title="Queue API test podcast",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        episode = Episode.objects.create(
            podcast=podcast,
            title="Remove me",
            status=Episode.PublicationStatus.PUBLISHED,
        )
        queue = Queue.objects.create(owner=user)
        queue.add_item(str(episode.pk), AppLabel.EPISODE)
        url = reverse(
            "rest:rest_web:api_apps:queue_web_api:queue-item-remove",
            kwargs={"episode_id": episode.pk},
        )
        request = APIRequestFactory().delete(url)
        force_authenticate(request, user=user)

        response = QueueViewSet.as_view({"delete": "remove"})(
            request,
            episode_id=episode.pk,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"deleted": 1})
        self.assertFalse(queue.items.filter(track_id=episode.pk).exists())

    def test_add_podcast_response_excludes_unpublished_episode_metadata(self):
        user = get_user_model().objects.create(
            username="queue-discovery-listener",
            clerk_user_id="clerk_queue_discovery_listener",
        )
        podcast = Podcast.objects.create(
            title="Queue discovery podcast",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        published = Episode.objects.create(
            podcast=podcast,
            title="Published queue episode",
            status=Episode.PublicationStatus.PUBLISHED,
        )
        Episode.objects.create(
            podcast=podcast,
            title="Private queue draft",
            status=Episode.PublicationStatus.DRAFT,
        )
        url = reverse("rest:rest_web:api_apps:queue_web_api:queue-add")
        request = APIRequestFactory().post(
            url,
            {
                "item_id": str(podcast.pk),
                "app_label": AppLabel.PODCAST,
                "override": False,
            },
            format="json",
        )
        force_authenticate(request, user=user)

        response = QueueViewSet.as_view({"post": "add"})(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["track"]["id"], str(published.pk))
        self.assertNotIn("Private queue draft", str(response.data))

    def test_list_hides_saved_item_after_episode_is_unpublished(self):
        user = get_user_model().objects.create(
            username="queue-unpublish-listener",
            clerk_user_id="clerk_queue_unpublish_listener",
        )
        podcast = Podcast.objects.create(
            title="Queue unpublish podcast",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        episode = Episode.objects.create(
            podcast=podcast,
            title="Later archived",
            status=Episode.PublicationStatus.PUBLISHED,
        )
        queue = Queue.objects.create(owner=user)
        queue.add_item(str(episode.pk), AppLabel.EPISODE)
        episode.status = Episode.PublicationStatus.ARCHIVED
        episode.save(update_fields=("status", "updated"))
        url = reverse("rest:rest_web:api_apps:queue_web_api:queue")
        request = APIRequestFactory().get(url)
        force_authenticate(request, user=user)

        response = QueueViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["tracks"], [])
        self.assertTrue(queue.items.filter(track=episode).exists())
