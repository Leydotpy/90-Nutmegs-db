"""Content ownership and stable identifier boundaries for operator writes."""

from api.rest.dashboard.apps.podcasts.serializers import PodcastSerializer, SeasonSerializer
from django.contrib.auth import get_user_model
from django.forms import modelform_factory
from django.test import TestCase
from rest_framework.test import APIClient

from apps.posts.podcasts.models import Episode, Podcast, Season


class SeasonIdentityTests(TestCase):
    def setUp(self):
        self.first = Podcast.objects.create(title="First show", structure=Podcast.Structure.PARENT)
        self.second = Podcast.objects.create(
            title="Second show", structure=Podcast.Structure.PARENT
        )
        self.season = Season.objects.create(
            podcast=self.first, title="First season", slug="first-season", position=1
        )
        self.client = APIClient()
        self.client.force_authenticate(
            get_user_model().objects.create(
                username="content-identity-staff",
                clerk_user_id="clerk_content_identity_staff",
                is_staff=True,
            )
        )

    def test_direct_season_move_cannot_split_episode_ownership(self):
        episode = Episode.objects.create(
            podcast=self.first, season=self.season, title="Episode stays with its show"
        )

        response = self.client.patch(
            f"/api/rest/dashboard/apps/podcasts/seasons/{self.season.pk}/",
            {"podcast": str(self.second.pk)},
            format="json",
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("podcast", response.data)
        self.season.refresh_from_db()
        episode.refresh_from_db()
        self.assertEqual(self.season.podcast, self.first)
        self.assertEqual(episode.podcast, self.first)

    def test_empty_season_owner_is_stable_before_episodes_are_attached(self):
        serializer = SeasonSerializer(
            self.season, data={"podcast": str(self.second.pk)}, partial=True
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("podcast", serializer.errors)

    def test_season_slug_cannot_invalidate_existing_public_selection(self):
        response = self.client.patch(
            f"/api/rest/dashboard/apps/podcasts/seasons/{self.season.pk}/",
            {"slug": "replacement-slug"},
            format="json",
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("slug", response.data)
        self.season.refresh_from_db()
        self.assertEqual(self.season.slug, "first-season")

    def test_admin_form_rejects_owner_and_slug_changes(self):
        form_class = modelform_factory(Season, fields=("podcast", "title", "slug", "position"))
        form = form_class(
            instance=self.season,
            data={
                "podcast": str(self.second.pk),
                "title": self.season.title,
                "slug": "replacement-slug",
                "position": 1,
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("podcast", form.errors)
        self.assertIn("slug", form.errors)

    def test_metadata_and_repeated_identity_updates_remain_supported(self):
        serializer = SeasonSerializer(
            self.season,
            data={
                "podcast": str(self.first.pk),
                "slug": "first-season",
                "title": "Renamed season",
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        saved = serializer.save()
        self.assertEqual(saved.title, "Renamed season")
        self.assertEqual(saved.podcast, self.first)
        self.assertEqual(saved.slug, "first-season")

    def test_create_accepts_an_explicit_stable_slug(self):
        serializer = SeasonSerializer(
            data={
                "podcast": str(self.second.pk),
                "title": "New season",
                "slug": "new-season",
                "position": 1,
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.save().slug, "new-season")

    def test_legacy_child_move_remains_one_atomic_graph_transition(self):
        serializer = PodcastSerializer(
            data={
                "title": "Legacy season",
                "structure": Podcast.Structure.CHILD,
                "parent": str(self.first.pk),
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        child = serializer.save()
        season = Season.objects.get(legacy_podcast=child)
        episode = Episode.objects.create(podcast=self.first, season=season, title="Legacy episode")
        original_slug = season.slug
        move = PodcastSerializer(child, data={"parent": str(self.second.pk)}, partial=True)

        self.assertTrue(move.is_valid(), move.errors)
        move.save()

        child.refresh_from_db()
        season.refresh_from_db()
        episode.refresh_from_db()
        self.assertEqual(child.parent, self.second)
        self.assertEqual(season.podcast, self.second)
        self.assertEqual(episode.podcast, self.second)
        self.assertEqual(episode.season, season)
        self.assertEqual(season.slug, original_slug)

    def test_stale_season_metadata_update_does_not_undo_a_legacy_move(self):
        serializer = PodcastSerializer(
            data={
                "title": "Legacy season",
                "structure": Podcast.Structure.CHILD,
                "parent": str(self.first.pk),
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        child = serializer.save()
        season = Season.objects.get(legacy_podcast=child)
        episode = Episode.objects.create(podcast=self.first, season=season, title="Moving episode")
        metadata = SeasonSerializer(season, data={"title": "Updated canonical title"}, partial=True)
        self.assertTrue(metadata.is_valid(), metadata.errors)
        move = PodcastSerializer(child, data={"parent": str(self.second.pk)}, partial=True)
        self.assertTrue(move.is_valid(), move.errors)
        move.save()

        metadata.save()

        season.refresh_from_db()
        episode.refresh_from_db()
        self.assertEqual(season.podcast, self.second)
        self.assertEqual(episode.podcast, self.second)
        self.assertEqual(season.title, "Updated canonical title")
