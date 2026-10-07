import datetime
from unittest import mock

from apps.media.audio.models import Audio
from apps.media.models import PlayList
from apps.memberships.models import Plan
from apps.posts.podcasts.models import Episode, Podcast, Season
from apps.promotions.models import (
    BannerSyncStatus,
    HandPickedPostList,
    OrderedPodcast,
)
from apps.promotions.models import (
    Image as PromotionImage,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from api.rest.web.apps.podcasts.serializers import PodcastDetailSerializer


class PodcastDetailPrivacyTests(TestCase):
    def test_public_detail_exposes_only_subscriber_count(self):
        podcast = Podcast.objects.create(title="Privacy test podcast")
        users = [
            get_user_model().objects.create_user(
                email=f"listener-{index}@example.com",
                username=f"listener-{index}",
                password="test-password",
                clerk_user_id=f"clerk-listener-{index}",
            )
            for index in range(2)
        ]
        podcast.subscribers.add(*users)
        request = RequestFactory().get("/podcasts/privacy-test/")
        request.user = AnonymousUser()

        data = PodcastDetailSerializer(
            podcast,
            context={"request": request, "paginated_episodes": {}},
        ).data

        self.assertEqual(data["subscriber_count"], 2)
        self.assertNotIn("subscriptions", data)
        rendered = str(data)
        for user in users:
            self.assertNotIn(user.email, rendered)
            self.assertNotIn(user.username, rendered)


class PublicEpisodePublicationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.now = timezone.now()
        self.podcast = Podcast.objects.create(
            title="Publication API podcast",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=self.now - datetime.timedelta(hours=1),
        )
        self.plan = Plan.objects.create(name="Publication fan", tier=Plan.Level.FAN)

    def episode(
        self,
        title,
        *,
        status,
        visibility=Episode.Visibility.PUBLIC,
        season=None,
    ):
        return Episode.objects.create(
            podcast=self.podcast,
            season=season,
            title=title,
            status=status,
            visibility=visibility,
            published_at=self.now - datetime.timedelta(hours=1),
            premium_available_at=self.now - datetime.timedelta(hours=1),
            public_available_at=(
                self.now - datetime.timedelta(hours=1)
                if visibility == Episode.Visibility.PUBLIC
                else None
            ),
            required_plan=(self.plan if visibility == Episode.Visibility.PLAN else None),
        )

    def test_public_list_excludes_draft_and_archived_metadata(self):
        published = self.episode(
            "Published",
            status=Episode.PublicationStatus.PUBLISHED,
        )
        premium = self.episode(
            "Premium discoverable",
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PLAN,
        )
        draft = self.episode("Draft", status=Episode.PublicationStatus.DRAFT)
        archived = self.episode("Archived", status=Episode.PublicationStatus.ARCHIVED)

        response = self.client.get(f"/api/rest/web/apps/podcast/{self.podcast.slug}/episodes/")

        self.assertEqual(response.status_code, 200)
        identifiers = {str(item["id"]) for item in response.data["results"]}
        self.assertEqual(identifiers, {str(published.pk), str(premium.pk)})
        self.assertNotIn(str(draft.pk), identifiers)
        self.assertNotIn(str(archived.pk), identifiers)

    def test_public_detail_hides_draft_but_keeps_premium_metadata_discoverable(self):
        draft = self.episode("Draft detail", status=Episode.PublicationStatus.DRAFT)
        premium = self.episode(
            "Premium detail",
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PLAN,
        )

        hidden = self.client.get(f"/api/rest/web/apps/podcast/episode/{draft.slug}/")
        discoverable = self.client.get(f"/api/rest/web/apps/podcast/episode/{premium.slug}/")

        self.assertEqual(hidden.status_code, 404)
        self.assertEqual(discoverable.status_code, 200)
        self.assertFalse(discoverable.data["user_has_access"])

    def test_public_duration_aggregates_ignore_unpublished_audio(self):
        published = self.episode(
            "Published duration",
            status=Episode.PublicationStatus.PUBLISHED,
        )
        draft = self.episode(
            "Draft duration",
            status=Episode.PublicationStatus.DRAFT,
        )
        for episode, duration in ((published, 30), (draft, 300)):
            Audio.objects.create(
                episode=episode,
                name=f"{episode.title} master",
                duration=duration,
                quality=Audio.Quality.HIGH,
                file=f"episodes/{episode.pk}/master.mp3",
                master=True,
            )
        playlist = PlayList.objects.create(name="Publication duration playlist")
        playlist.items.add(published, draft)

        self.assertEqual(self.podcast.get_raw_duration(), 30)
        self.assertEqual(playlist.get_raw_duration(), 30)

    def test_detail_selects_explicit_season_and_serializes_canonical_seasons(self):
        first = Season.objects.create(
            podcast=self.podcast,
            title="Season one",
            slug="season-one",
            number=1,
            position=1,
            published_at=self.now - datetime.timedelta(hours=2),
        )
        second = Season.objects.create(
            podcast=self.podcast,
            title="Season two",
            slug="season-two",
            number=2,
            position=2,
            published_at=self.now - datetime.timedelta(hours=1),
        )
        first_episode = self.episode(
            "First season episode",
            status=Episode.PublicationStatus.PUBLISHED,
            season=first,
        )
        second_episode = self.episode(
            "Second season episode",
            status=Episode.PublicationStatus.PUBLISHED,
            season=second,
        )

        response = self.client.get(
            f"/api/rest/web/apps/podcast/{self.podcast.slug}/",
            {"season": second.slug},
        )

        self.assertEqual(response.status_code, 200)
        episode_ids = {str(item["id"]) for item in response.data["episodes"]["results"]}
        self.assertEqual(episode_ids, {str(second_episode.pk)})
        self.assertNotIn(str(first_episode.pk), episode_ids)
        self.assertEqual(
            [season["slug"] for season in response.data["seasons"]],
            [first.slug, second.slug],
        )

    def test_draft_podcast_hides_published_episode_metadata(self):
        draft_podcast = Podcast.objects.create(title="Hidden draft show")
        hidden_episode = Episode.objects.create(
            podcast=draft_podcast,
            title="Published episode under draft show",
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PUBLIC,
            published_at=self.now,
            public_available_at=self.now,
        )

        podcast_response = self.client.get(f"/api/rest/web/apps/podcast/{draft_podcast.slug}/")
        episode_response = self.client.get(
            f"/api/rest/web/apps/podcast/episode/{hidden_episode.slug}/"
        )

        self.assertEqual(podcast_response.status_code, 404)
        self.assertEqual(episode_response.status_code, 404)

    def test_legacy_child_owned_episode_fails_closed_until_reconciled(self):
        parent = Podcast.objects.create(
            title="Legacy parent",
            structure=Podcast.Structure.PARENT,
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=self.now - datetime.timedelta(hours=1),
        )
        child = Podcast.objects.create(
            title="Unreconciled legacy child",
            structure=Podcast.Structure.CHILD,
            parent=parent,
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=self.now - datetime.timedelta(hours=1),
        )
        episode = Episode.objects.create(
            podcast=child,
            title="Unreconciled child-owned episode",
            status=Episode.PublicationStatus.PUBLISHED,
            public_available_at=self.now - datetime.timedelta(hours=1),
        )

        response = self.client.get(f"/api/rest/web/apps/podcast/episode/{episode.slug}/")

        self.assertEqual(response.status_code, 404)

    def test_publication_window_is_resolved_at_request_time(self):
        opens_at = self.now + datetime.timedelta(hours=2)
        scheduled = Podcast.objects.create(
            title="Opens without a process restart",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=opens_at,
        )

        with mock.patch(
            "apps.posts.podcasts.models.timezone.now",
            return_value=opens_at + datetime.timedelta(seconds=1),
        ):
            response = self.client.get(f"/api/rest/web/apps/podcast/{scheduled.slug}/")

        self.assertEqual(response.status_code, 200)

    def test_handpicked_promotions_exclude_unpublished_podcasts(self):
        published = Podcast.objects.create(
            title="Published hand-picked show",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=self.now - datetime.timedelta(hours=1),
        )
        draft = Podcast.objects.create(title="Draft hand-picked show")
        promotion = HandPickedPostList.objects.create(name="Safe hand-picked list")
        OrderedPodcast.objects.create(list=promotion, podcast=draft, display_order=1)
        OrderedPodcast.objects.create(list=promotion, podcast=published, display_order=2)

        response = self.client.get("/api/rest/web/apps/podcast/handpicked/")

        self.assertEqual(response.status_code, 200)
        items = response.data["results"][0]["items"]
        self.assertEqual([str(item["id"]) for item in items], [str(published.pk)])

    def test_ready_banners_exclude_unpublished_linked_podcasts(self):
        published = Podcast.objects.create(
            title="Published banner show",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=self.now - datetime.timedelta(hours=1),
        )
        draft = Podcast.objects.create(title="Draft banner show")
        banners = [
            PromotionImage.objects.create(
                name=name,
                title=name,
                podcast=podcast,
                banner_status=BannerSyncStatus.READY,
                banner_url=f"https://cdn.example.com/{name}.png",
            )
            for name, podcast in (
                ("unlinked", None),
                ("published", published),
                ("draft", draft),
            )
        ]

        response = self.client.get("/api/rest/web/apps/podcast/promotions/")

        self.assertEqual(response.status_code, 200)
        banner_ids = {
            str(item["resource_id"])
            for item in response.data["promotions"]["banners"]
        }
        self.assertEqual(banner_ids, {str(banners[0].pk), str(banners[1].pk)})
