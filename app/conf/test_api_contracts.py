"""SF-01 compatibility contracts exercised through the real URL configuration.

Literal paths are deliberate: reversing a renamed route would hide a client
compatibility regression. Existing broken playlist handlers and shadowed audio
actions are tracked in the implementation ledger, not blessed by these tests.
"""

from datetime import timedelta
from uuid import UUID

from apps.media.offline.models import Device, License, Package
from apps.posts.podcasts.models import Episode, Podcast
from apps.queue.models import Queue, QueueItem
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from django.urls import Resolver404, resolve
from django.utils import timezone
from rest_framework.test import APIClient

RESOURCE_ID = "11111111-1111-4111-8111-111111111111"
PUBLIC = "/api/rest/web/apps"
DASHBOARD = "/api/rest/dashboard/apps/podcasts"


class LiteralRouteCompatibilityTests(SimpleTestCase):
    def test_public_content_paths_keep_slug_lookups_and_playback_spelling(self):
        cases = (
            ("podcast/matchday-show/", "podcast-detail", {"slug": "matchday-show"}),
            (
                "podcast/matchday-show/episodes/",
                "episodes-list",
                {"slug": "matchday-show"},
            ),
            ("podcast/episode/final-whistle/", "episode-detail", {"slug": "final-whistle"}),
            (
                "podcast/episode/final-whistle/update-playback",
                "episode-update-playback",
                {"slug": "final-whistle"},
            ),
            ("podcast/recently-played/", "recently-played", {}),
            ("podcast/resume-playback/", "resume-playback", {}),
            ("profile/subscribe/", "user-subscription", {}),
            ("profile/subscriptions/podcast/", "subscriptions", {}),
        )
        for suffix, name, kwargs in cases:
            with self.subTest(path=suffix):
                match = resolve(f"{PUBLIC}/{suffix}")
                self.assertEqual(match.url_name, name)
                self.assertEqual(match.kwargs, kwargs)

    def test_protected_media_paths_keep_uuid_and_task_id_converters(self):
        cases = (
            (
                f"streaming/episodes/{RESOURCE_ID}/stream/",
                "stream_episode_progressive",
                {"episode_id": UUID(RESOURCE_ID)},
            ),
            ("offline/devices/register/", "register_device", {}),
            ("offline/packages/request/", "request_offline_package", {}),
            (
                "offline/packages/status/worker-task-42/",
                "packaging_status",
                {"task_id": "worker-task-42"},
            ),
            (
                f"offline/licenses/{RESOURCE_ID}/revoke/",
                "revoke_offline_license",
                {"license_id": UUID(RESOURCE_ID)},
            ),
        )
        for suffix, name, kwargs in cases:
            with self.subTest(path=suffix):
                match = resolve(f"{PUBLIC}/media/{suffix}")
                self.assertEqual(match.url_name, name)
                self.assertEqual(match.kwargs, kwargs)

    def test_queue_paths_expose_only_the_explicit_actions(self):
        cases = (
            ("", "queue", {}, {"get": "list"}),
            ("add/", "queue-add", {}, {"post": "add"}),
            ("clear/", "queue-clear", {}, {"put": "clear"}),
            (
                f"{RESOURCE_ID}/remove/",
                "queue-item-remove",
                {"episode_id": UUID(RESOURCE_ID)},
                {"delete": "remove"},
            ),
        )
        for suffix, name, kwargs, actions in cases:
            with self.subTest(path=suffix):
                match = resolve(f"{PUBLIC}/queue/{suffix}")
                self.assertEqual(match.url_name, name)
                self.assertEqual(match.kwargs, kwargs)
                # DRF adds HEAD to GET actions when an earlier test dispatches
                # the shared callback. It is not a separate mutation action.
                self.assertEqual(
                    {
                        method: action
                        for method, action in match.func.actions.items()
                        if method != "head"
                    },
                    actions,
                )

    def test_dashboard_routes_keep_crud_and_nested_content_actions(self):
        collection = {"get": "list", "post": "create"}
        detail = {
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }
        cases = (
            ("/", "podcasts-list", {}, collection),
            (f"/{RESOURCE_ID}/", "podcasts-detail", {"pk": RESOURCE_ID}, detail),
            ("/seasons/", "season-list", {}, collection),
            (f"/seasons/{RESOURCE_ID}/", "season-detail", {"pk": RESOURCE_ID}, detail),
            ("/episodes/", "episode-list", {}, collection),
            (f"/episodes/{RESOURCE_ID}/", "episode-detail", {"pk": RESOURCE_ID}, detail),
            (
                f"/{RESOURCE_ID}/episodes/",
                "podcasts-episodes",
                {"pk": RESOURCE_ID},
                {"get": "episodes"},
            ),
            (
                f"/{RESOURCE_ID}/seasons/",
                "podcasts-seasons",
                {"pk": RESOURCE_ID},
                {"get": "seasons"},
            ),
            (
                f"/episodes/{RESOURCE_ID}/audios/",
                "episode-audios",
                {"pk": RESOURCE_ID},
                {"get": "audios"},
            ),
            (
                f"/episodes/{RESOURCE_ID}/upload_audio/",
                "episode-upload-audio",
                {"pk": RESOURCE_ID},
                {"post": "upload_audio"},
            ),
        )
        for suffix, name, kwargs, actions in cases:
            with self.subTest(path=suffix):
                match = resolve(f"{DASHBOARD}{suffix}")
                self.assertEqual(match.url_name, name)
                self.assertEqual(match.kwargs, kwargs)
                self.assertEqual(
                    {
                        method: action
                        for method, action in match.func.actions.items()
                        if method != "head"
                    },
                    actions,
                )

    def test_uuid_only_routes_reject_slugs_before_dispatch(self):
        paths = (
            f"{PUBLIC}/queue/final-whistle/remove/",
            f"{PUBLIC}/media/streaming/episodes/final-whistle/stream/",
            f"{PUBLIC}/media/offline/licenses/license-slug/revoke/",
        )
        for path in paths:
            with self.subTest(path=path), self.assertRaises(Resolver404):
                resolve(path)


class RoutedOwnershipContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.listener = get_user_model().objects.create(
            username="contract-listener", clerk_user_id="clerk_contract_listener"
        )
        cls.other_listener = get_user_model().objects.create(
            username="contract-other-listener", clerk_user_id="clerk_contract_other_listener"
        )
        cls.podcast = Podcast.objects.create(
            title="Contract show",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now() - timedelta(hours=1),
        )
        cls.first = Episode.objects.create(
            podcast=cls.podcast,
            title="First contract episode",
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PUBLIC,
            public_available_at=timezone.now() - timedelta(hours=1),
        )
        cls.second = Episode.objects.create(
            podcast=cls.podcast,
            title="Second contract episode",
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PUBLIC,
            public_available_at=timezone.now() - timedelta(hours=1),
        )

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.client.force_authenticate(self.listener)
        self.own_queue = Queue.objects.create(owner=self.listener)
        self.other_queue = Queue.objects.create(owner=self.other_listener)
        for queue in (self.own_queue, self.other_queue):
            QueueItem.objects.create(queue=queue, track=self.first, position=1)
            QueueItem.objects.create(queue=queue, track=self.second, position=2)

    def queue_tracks(self, queue):
        return list(queue.items.order_by("position").values_list("track_id", flat=True))

    def test_remove_is_owner_scoped_and_repeatable(self):
        url = f"{PUBLIC}/queue/{self.first.pk}/remove/?queue_id={self.other_queue.pk}"

        removed = self.client.delete(url)
        repeated = self.client.delete(url)

        self.assertEqual(removed.status_code, 200)
        self.assertEqual(removed.data, {"deleted": 1})
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(repeated.data, {"deleted": 0})
        self.assertEqual(self.queue_tracks(self.own_queue), [self.second.pk])
        self.assertEqual(self.queue_tracks(self.other_queue), [self.first.pk, self.second.pk])

    def test_clear_ignores_supplied_other_owner_and_queue(self):
        response = self.client.put(
            f"{PUBLIC}/queue/clear/",
            {"owner": self.other_listener.pk, "queue_id": self.other_queue.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"status": "cleared"})
        self.assertFalse(self.own_queue.items.exists())
        self.assertEqual(self.queue_tracks(self.other_queue), [self.first.pk, self.second.pk])

    def test_anonymous_list_is_scoped_to_the_current_session(self):
        first_client, second_client = APIClient(), APIClient()
        first_queue = Queue.objects.create(session_key=first_client.session.session_key)
        second_queue = Queue.objects.create(session_key=second_client.session.session_key)
        QueueItem.objects.create(queue=first_queue, track=self.first)
        QueueItem.objects.create(queue=second_queue, track=self.second)

        response = first_client.get(
            f"{PUBLIC}/queue/?queue_id={second_queue.pk}&owner={self.listener.pk}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["track"]["id"] for item in response.data["tracks"]], [str(self.first.pk)]
        )
        self.assertEqual(self.queue_tracks(first_queue), [self.first.pk])
        self.assertEqual(self.queue_tracks(second_queue), [self.second.pk])
        self.assertEqual(self.queue_tracks(self.own_queue), [self.first.pk, self.second.pk])

    def test_wrong_queue_methods_return_405_without_mutation(self):
        cases = (
            ("post", f"{PUBLIC}/queue/"),
            ("get", f"{PUBLIC}/queue/add/"),
            ("post", f"{PUBLIC}/queue/clear/"),
            ("get", f"{PUBLIC}/queue/{self.first.pk}/remove/"),
        )
        for method, path in cases:
            with self.subTest(method=method, path=path):
                response = getattr(self.client, method)(path)
                self.assertEqual(response.status_code, 405)
                self.assertEqual(self.queue_tracks(self.own_queue), [self.first.pk, self.second.pk])
                self.assertEqual(
                    self.queue_tracks(self.other_queue), [self.first.pk, self.second.pk]
                )

    def test_queue_validation_failure_does_not_change_existing_items(self):
        response = self.client.post(
            f"{PUBLIC}/queue/add/",
            {"item_id": str(self.first.pk), "app_label": "users.User"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("app_label", response.data)
        self.assertEqual(self.queue_tracks(self.own_queue), [self.first.pk, self.second.pk])

    def test_regular_listener_cannot_write_dashboard_content(self):
        for method in ("patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    f"{DASHBOARD}/episodes/{self.first.pk}/",
                    {"title": "Unauthorized replacement"},
                    format="json",
                )
                self.assertEqual(response.status_code, 403)
                self.first.refresh_from_db()
                self.assertEqual(self.first.title, "First contract episode")

    def test_follow_mutation_requires_authentication(self):
        client = APIClient()

        response = client.post(
            f"{PUBLIC}/profile/subscribe/",
            {"app_label": "podcasts.Podcast", "item_id": str(self.podcast.pk)},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(self.podcast.subscribers.exists())

    def test_read_only_and_follow_endpoints_reject_wrong_methods(self):
        cases = (
            ("post", f"{PUBLIC}/podcast/episode/{self.first.slug}/"),
            ("post", f"{PUBLIC}/media/streaming/episodes/{self.first.pk}/stream/"),
            ("get", f"{PUBLIC}/profile/subscribe/"),
        )
        for method, path in cases:
            with self.subTest(method=method, path=path):
                response = getattr(self.client, method)(path)
                self.assertEqual(response.status_code, 405)
        self.assertFalse(self.podcast.subscribers.exists())

    def test_offline_license_revocation_hides_other_owners_and_is_repeatable(self):
        package = Package.objects.create(
            episode=self.first,
            storage_key="fixtures/offline-package",
            encrypted_dek=b"synthetic-encrypted-test-material",
        )
        licenses = []
        for user in (self.listener, self.other_listener):
            device = Device.objects.create(
                user=user, device_id=f"device-{user.pk}", public_key_pem="synthetic-test-key"
            )
            licenses.append(
                License.objects.create(
                    user=user,
                    device=device,
                    package=package,
                    encrypted_dek_for_device=b"synthetic-wrapped-test-material",
                    expires_at=timezone.now() + timedelta(days=1),
                )
            )
        owned, other = licenses

        denied = self.client.post(f"{PUBLIC}/media/offline/licenses/{other.pk}/revoke/")
        self.assertEqual(denied.status_code, 404)
        other.refresh_from_db()
        self.assertFalse(other.revoked)
        for _ in range(2):
            response = self.client.post(f"{PUBLIC}/media/offline/licenses/{owned.pk}/revoke/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, {"status": "revoked"})
        owned.refresh_from_db()
        self.assertTrue(owned.revoked)
        self.assertEqual(License.objects.count(), 2)
