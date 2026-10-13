"""Exercise real login rotation, not a manually emitted login signal."""

from apps.posts.podcasts.models import Episode, Podcast
from apps.queue.models import Queue, QueueItem
from django.contrib.auth import authenticate, get_user_model, login
from django.http import JsonResponse
from django.test import TestCase, override_settings
from django.urls import path


def login_probe(request):
    user = authenticate(request, username=request.POST.get("username"), password="test-only")
    if user is None:
        return JsonResponse({"authenticated": False}, status=401)
    login(request, user)
    return JsonResponse({"authenticated": True})


urlpatterns = [path("login-probe/", login_probe)]


@override_settings(ROOT_URLCONF=__name__)
class LoginIdentityHandoffTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="login-listener", email="login@example.test", password="test-only"
        )
        session = self.client.session
        session["anonymous-marker"] = True
        session.save()
        self.old_key = session.session_key
        self.queue = Queue.objects.create(session_key=self.old_key)
        podcast = Podcast.objects.create(title="Login handoff")
        self.episode = Episode.objects.create(podcast=podcast, title="Saved anonymously")
        QueueItem.objects.create(queue=self.queue, track=self.episode, position=1, order=1)

    def test_login_rotates_session_and_transfers_only_its_anonymous_queue(self):
        unrelated = Queue.objects.create(session_key="another-browser")
        response = self.client.post(
            "/login-probe/", {"username": self.user.username, "session_key": unrelated.session_key}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.client.session.session_key, self.old_key)
        self.assertFalse(Queue.objects.filter(pk=self.queue.pk).exists())
        self.assertTrue(Queue.objects.filter(pk=unrelated.pk).exists())
        self.assertEqual(
            list(Queue.objects.get(owner=self.user).items.values_list("track_id", flat=True)),
            [self.episode.pk],
        )
        self.client.post("/login-probe/", {"username": self.user.username})
        self.assertEqual(QueueItem.objects.filter(queue__owner=self.user).count(), 1)

    def test_failed_login_keeps_anonymous_ownership(self):
        response = self.client.post("/login-probe/", {"username": "missing-user"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.client.session.session_key, self.old_key)
        self.assertTrue(Queue.objects.filter(pk=self.queue.pk, owner=None).exists())

    def test_switching_authenticated_users_never_claims_a_session_queue(self):
        self.client.force_login(self.user)
        owned_session = self.client.session.session_key
        other = get_user_model().objects.create_user(
            username="other-listener", email="other@example.test", password="test-only"
        )
        suspect = Queue.objects.create(session_key=owned_session)
        response = self.client.post("/login-probe/", {"username": other.username})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Queue.objects.filter(pk=suspect.pk, owner=None).exists())
        self.assertFalse(Queue.objects.filter(owner=other).exists())

    @override_settings(ROOT_URLCONF="conf.urls", SESSION_SAVE_EVERY_REQUEST=False)
    def test_liveness_with_session_cookie_does_not_query_the_database(self):
        with self.assertNumQueries(0):
            response = self.client.get("/health/live/")
        self.assertEqual(response.status_code, 200)
