import datetime
from unittest.mock import patch

from api.rest.web.apps.podcasts.serializers import PlayBackUpdateSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.utils import timezone

from apps.media.audio.models import Audio
from apps.posts.podcasts.models import Episode, PlayBack, Podcast
from apps.posts.podcasts.queries import new_releases, trending_episodes


class PlaybackTestCase(TestCase):
    def setUp(self):
        self.requests = RequestFactory()
        self.user = self.create_user("listener-one")
        self.other_user = self.create_user("listener-two")
        self.podcast = Podcast.objects.create(
            title="Playback test podcast",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now() - datetime.timedelta(hours=1),
        )

    @staticmethod
    def create_user(username):
        return get_user_model().objects.create_user(
            email=f"{username}@example.com",
            username=username,
            password="test-password",
            clerk_user_id=f"clerk-{username}",
        )

    def create_episode(self, title):
        return Episode.objects.create(
            podcast=self.podcast,
            title=title,
            status=Episode.PublicationStatus.PUBLISHED,
        )

    def request_for(self, user, ip_address=None):
        request = self.requests.get(
            "/playback/",
            REMOTE_ADDR=ip_address or "",
        )
        request.user = user
        return request


class EpisodePublicationSelectorTests(TestCase):
    def test_public_discovery_selectors_never_return_non_published_rows(self):
        now = timezone.now()
        podcast = Podcast.objects.create(
            title="Selector publication podcast",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=now - datetime.timedelta(hours=1),
        )
        published = Episode.objects.create(
            podcast=podcast,
            title="Published selector episode",
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PUBLIC,
            premium_available_at=now,
            public_available_at=now,
        )
        Episode.objects.create(
            podcast=podcast,
            title="Draft selector episode",
            status=Episode.PublicationStatus.DRAFT,
        )
        Episode.objects.create(
            podcast=podcast,
            title="Archived selector episode",
            status=Episode.PublicationStatus.ARCHIVED,
            public_available_at=now,
        )

        self.assertEqual(list(new_releases()), [published])
        self.assertEqual(list(trending_episodes()), [published])
        self.assertEqual(list(podcast.get_discoverable_episodes()), [published])


class PlaybackIdentityTests(PlaybackTestCase):
    def test_authenticated_progress_is_keyed_by_user_and_episode_not_ip(self):
        episode = self.create_episode("Identity episode")

        first = PlayBack.objects.update_progress(
            user=self.user,
            episode_id=episode.pk,
            ip_address="192.0.2.10",
            seconds=15,
        )
        second = PlayBack.objects.update_progress(
            user=self.user,
            episode_id=episode.pk,
            ip_address="198.51.100.20",
            seconds=42,
        )

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(
            PlayBack.objects.filter(user=self.user, episode=episode).count(),
            1,
        )
        second.refresh_from_db()
        self.assertEqual(second.current_timestamp, 42)
        self.assertEqual(second.ip_address, "198.51.100.20")

    def test_authenticated_users_do_not_share_progress_on_the_same_ip(self):
        episode = self.create_episode("Shared address episode")

        first = PlayBack.objects.update_progress(
            user=self.user,
            episode_id=episode.pk,
            ip_address="203.0.113.7",
            seconds=12,
        )
        second = PlayBack.objects.update_progress(
            user=self.other_user,
            episode_id=episode.pk,
            ip_address="203.0.113.7",
            seconds=31,
        )

        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(PlayBack.objects.filter(episode=episode).count(), 2)

    def test_anonymous_progress_is_keyed_by_ip_and_episode(self):
        episode = self.create_episode("Anonymous identity episode")

        first = PlayBack.objects.update_progress(
            user=AnonymousUser(),
            episode_id=episode.pk,
            ip_address="192.0.2.30",
            seconds=8,
        )
        updated = PlayBack.objects.update_progress(
            user=AnonymousUser(),
            episode_id=episode.pk,
            ip_address="192.0.2.30",
            seconds=22,
        )
        separate = PlayBack.objects.update_progress(
            user=AnonymousUser(),
            episode_id=episode.pk,
            ip_address="192.0.2.31",
            seconds=5,
        )

        self.assertEqual(first.pk, updated.pk)
        self.assertNotEqual(first.pk, separate.pk)
        self.assertIsNone(updated.user_id)
        self.assertEqual(PlayBack.objects.filter(episode=episode).count(), 2)

    def test_recent_history_separates_authenticated_and_anonymous_identity(self):
        episode = self.create_episode("Separated history episode")
        authenticated = PlayBack.objects.create(
            user=self.user,
            episode=episode,
            ip_address="203.0.113.19",
            current_timestamp=50,
        )
        anonymous = PlayBack.objects.create(
            user=None,
            episode=episode,
            ip_address="203.0.113.19",
            current_timestamp=25,
        )
        PlayBack.objects.create(
            user=self.other_user,
            episode=episode,
            ip_address="203.0.113.19",
            current_timestamp=10,
        )

        authenticated_history = list(
            PlayBack.objects.get_recently_played(self.request_for(self.user, "203.0.113.19"))
        )
        anonymous_history = list(
            PlayBack.objects.get_recently_played(self.request_for(AnonymousUser(), "203.0.113.19"))
        )

        self.assertEqual(authenticated_history, [authenticated])
        self.assertEqual(anonymous_history, [anonymous])

    def test_anonymous_history_without_an_ip_returns_no_rows(self):
        episode = self.create_episode("Missing identity episode")
        PlayBack.objects.create(
            user=None,
            episode=episode,
            ip_address=None,
            current_timestamp=20,
        )

        history = PlayBack.objects.get_recently_played(self.request_for(AnonymousUser()))

        self.assertFalse(history.exists())


class PlaybackProgressTests(PlaybackTestCase):
    def add_master_audio(self, episode, duration):
        return Audio.objects.create(
            episode=episode,
            name="Master audio",
            duration=duration,
            quality=Audio.Quality.HIGH,
            file=f"episodes/{episode.pk}/master.mp3",
            master=True,
        )

    def test_progress_rejects_negative_positions(self):
        episode = self.create_episode("Negative progress episode")

        with self.assertRaisesMessage(ValueError, "seconds cannot be negative"):
            PlayBack.objects.update_progress(
                user=self.user,
                episode_id=episode.pk,
                ip_address="192.0.2.40",
                seconds=-1,
            )

        self.assertFalse(PlayBack.objects.filter(episode=episode).exists())

    def test_progress_rejects_fractional_positions_without_truncating(self):
        episode = self.create_episode("Fractional progress episode")

        with self.assertRaisesMessage(ValueError, "seconds must be an integer"):
            PlayBack.objects.update_progress(
                user=self.user,
                episode_id=episode.pk,
                ip_address="192.0.2.39",
                seconds=1.5,
            )

        self.assertFalse(PlayBack.objects.filter(episode=episode).exists())

    def test_progress_is_bounded_by_known_duration(self):
        episode = self.create_episode("Bounded progress episode")
        self.add_master_audio(episode, duration=100)

        playback = PlayBack.objects.update_progress(
            user=self.user,
            episode_id=episode.pk,
            ip_address="192.0.2.41",
            seconds=140,
        )

        self.assertEqual(playback.current_timestamp, 100)
        self.assertTrue(playback.is_completed)

    def test_client_completion_flag_requires_duration_threshold(self):
        episode = self.create_episode("Completion threshold episode")
        self.add_master_audio(episode, duration=100)

        below_threshold = PlayBack.objects.update_progress(
            user=self.user,
            episode_id=episode.pk,
            ip_address="192.0.2.42",
            seconds=89,
            is_completed=True,
        )
        self.assertFalse(below_threshold.is_completed)

        at_threshold = PlayBack.objects.update_progress(
            user=self.user,
            episode_id=episode.pk,
            ip_address="192.0.2.42",
            seconds=90,
            is_completed=False,
        )
        self.assertTrue(at_threshold.is_completed)

    def test_completion_does_not_regress_on_a_later_checkpoint(self):
        episode = self.create_episode("Sticky completion episode")
        self.add_master_audio(episode, duration=100)
        PlayBack.objects.update_progress(
            user=self.user,
            episode_id=episode.pk,
            ip_address="192.0.2.43",
            seconds=95,
        )

        playback = PlayBack.objects.update_progress(
            user=self.user,
            episode_id=episode.pk,
            ip_address="192.0.2.44",
            seconds=15,
            is_completed=False,
        )

        self.assertEqual(playback.current_timestamp, 15)
        self.assertTrue(playback.is_completed)

    def test_unverified_completion_without_duration_is_not_accepted(self):
        episode = self.create_episode("Unknown duration episode")

        playback = PlayBack.objects.update_progress(
            user=self.user,
            episode_id=episode.pk,
            ip_address="192.0.2.45",
            seconds=300,
            is_completed=True,
        )

        self.assertFalse(playback.is_completed)


class PlaybackSelectionTests(PlaybackTestCase):
    def test_recent_and_uncompleted_selectors_share_ordering_and_identity(self):
        episodes = [
            self.create_episode("Old incomplete"),
            self.create_episode("Completed"),
            self.create_episode("Middle incomplete"),
            self.create_episode("New incomplete"),
        ]
        rows = [
            PlayBack.objects.create(
                user=self.user,
                episode=episode,
                current_timestamp=index * 10,
                is_completed=index == 2,
            )
            for index, episode in enumerate(episodes, start=1)
        ]
        now = timezone.now()
        for index, row in enumerate(rows):
            PlayBack.objects.filter(pk=row.pk).update(
                last_played_at=now - datetime.timedelta(minutes=10 - index)
            )

        request = self.request_for(self.user, "192.0.2.50")

        recent = list(PlayBack.objects.get_recently_played(request))
        uncompleted = list(PlayBack.objects.get_uncompleted(request, limit=3))

        self.assertEqual(recent, list(reversed(rows)))
        self.assertEqual(uncompleted, [rows[3], rows[2], rows[0]])

    def test_history_hides_saved_row_after_episode_is_unpublished(self):
        episode = self.create_episode("Later archived history")
        PlayBack.objects.create(
            user=self.user,
            episode=episode,
            current_timestamp=30,
        )
        episode.status = Episode.PublicationStatus.ARCHIVED
        episode.save(update_fields=("status", "updated"))

        history = PlayBack.objects.get_recently_played(self.request_for(self.user, "192.0.2.51"))

        self.assertFalse(history.exists())


class PlaybackReceiverTests(PlaybackTestCase):
    @patch("apps.posts.podcasts.receivers.invalidate_user_recommendations")
    def test_authenticated_progress_invalidates_recommendations(self, invalidate):
        episode = self.create_episode("Invalidation episode")

        playback = PlayBack.objects.create(user=self.user, episode=episode)

        invalidate.assert_called_once_with(self.user.pk)
        self.assertEqual(playback.user, self.user)

    @patch("apps.posts.podcasts.receivers.invalidate_user_recommendations")
    def test_anonymous_progress_does_not_invalidate_user_cache(self, invalidate):
        episode = self.create_episode("Anonymous invalidation episode")

        PlayBack.objects.create(
            user=None,
            episode=episode,
            ip_address="192.0.2.60",
        )

        invalidate.assert_not_called()


class PlaybackSerializerValidationTests(SimpleTestCase):
    def test_negative_progress_is_rejected_at_the_api_boundary(self):
        serializer = PlayBackUpdateSerializer(data={"seconds": -1, "is_completed": False})

        self.assertFalse(serializer.is_valid())
        self.assertIn("seconds", serializer.errors)
