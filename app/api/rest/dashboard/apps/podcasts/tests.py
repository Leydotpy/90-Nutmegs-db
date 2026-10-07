"""Authorization and publication regressions for podcast dashboard endpoints."""

import datetime

from apps.category.models import Category
from apps.memberships.models import Plan
from apps.posts.models import BasePost
from apps.posts.podcasts.models import Episode, Podcast, Season
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from api.rest.dashboard.apps.podcasts.serializers import (
    EpisodeSerializer,
    PodcastSerializer,
    SeasonSerializer,
)


class PodcastDashboardAuthorizationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.podcast = Podcast.objects.create(title="Dashboard permissions")

    def test_non_staff_user_cannot_list_dashboard_podcast_episodes(self):
        user = get_user_model().objects.create(
            username="ordinary-listener",
            clerk_user_id="clerk_ordinary_listener",
        )
        self.client.force_authenticate(user)

        response = self.client.get(f"/api/rest/dashboard/apps/podcasts/{self.podcast.pk}/episodes/")

        self.assertEqual(response.status_code, 403)

    def test_staff_user_retains_dashboard_podcast_episode_access(self):
        user = get_user_model().objects.create(
            username="dashboard-staff",
            clerk_user_id="clerk_dashboard_staff",
            is_staff=True,
        )
        self.client.force_authenticate(user)

        response = self.client.get(f"/api/rest/dashboard/apps/podcasts/{self.podcast.pk}/episodes/")

        self.assertEqual(response.status_code, 200)


class SeasonDashboardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.now = timezone.now()
        self.podcast = Podcast.objects.create(
            title="Season dashboard show",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=self.now,
        )
        self.staff = get_user_model().objects.create(
            username="season-dashboard-staff",
            clerk_user_id="clerk_season_dashboard_staff",
            is_staff=True,
        )

    def test_staff_can_create_and_list_explicit_seasons(self):
        self.client.force_authenticate(self.staff)

        created = self.client.post(
            "/api/rest/dashboard/apps/podcasts/seasons/",
            {
                "podcast": str(self.podcast.pk),
                "title": "Season one",
                "slug": "season-one",
                "number": 1,
                "position": 1,
                "published_at": self.now.isoformat(),
            },
            format="json",
        )
        listed = self.client.get("/api/rest/dashboard/apps/podcasts/seasons/")

        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(Season.objects.get().podcast, self.podcast)

    def test_legacy_child_dashboard_write_projects_to_canonical_season(self):
        parent = Podcast.objects.create(
            title="Legacy parent",
            structure=BasePost.Structure.PARENT,
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=self.now,
        )
        serializer = PodcastSerializer(
            data={
                "title": "Legacy child season",
                "structure": BasePost.Structure.CHILD,
                "parent": str(parent.pk),
                "status": Podcast.PublicationStatus.PUBLISHED,
                "published_at": self.now.isoformat(),
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        child = serializer.save()
        season = Season.objects.get(legacy_podcast=child)
        self.assertEqual(season.podcast, parent)
        self.assertEqual(season.title, child.title)
        self.assertEqual(season.position, 1)

    def test_legacy_child_episode_write_uses_root_podcast_and_explicit_season(self):
        parent = Podcast.objects.create(
            title="Legacy episode parent",
            structure=BasePost.Structure.PARENT,
        )
        child_serializer = PodcastSerializer(
            data={
                "title": "Legacy episode season",
                "structure": BasePost.Structure.CHILD,
                "parent": str(parent.pk),
            }
        )
        self.assertTrue(child_serializer.is_valid(), child_serializer.errors)
        child = child_serializer.save()

        episode_serializer = EpisodeSerializer(
            data={
                "podcast": str(child.pk),
                "title": "Written through the legacy season id",
            }
        )
        self.assertTrue(episode_serializer.is_valid(), episode_serializer.errors)
        episode = episode_serializer.save()
        season = Season.objects.get(legacy_podcast=child)

        self.assertEqual(episode.podcast, parent)
        self.assertEqual(episode.season, season)
        self.assertEqual(list(child.get_episodes()), [episode])

    def test_moving_legacy_child_moves_all_linked_episodes_to_new_parent(self):
        first_parent = Podcast.objects.create(
            title="First legacy parent",
            structure=BasePost.Structure.PARENT,
        )
        second_parent = Podcast.objects.create(
            title="Second legacy parent",
            structure=BasePost.Structure.PARENT,
        )
        child_serializer = PodcastSerializer(
            data={
                "title": "Movable legacy season",
                "structure": BasePost.Structure.CHILD,
                "parent": str(first_parent.pk),
            }
        )
        self.assertTrue(child_serializer.is_valid(), child_serializer.errors)
        child = child_serializer.save()
        season = Season.objects.get(legacy_podcast=child)
        episode = Episode.objects.create(
            podcast=first_parent,
            season=season,
            title="Episode that moves with its season",
        )

        move_serializer = PodcastSerializer(
            child,
            data={"parent": str(second_parent.pk)},
            partial=True,
        )
        self.assertTrue(move_serializer.is_valid(), move_serializer.errors)
        move_serializer.save()

        season.refresh_from_db()
        episode.refresh_from_db()
        self.assertEqual(season.podcast, second_parent)
        self.assertEqual(episode.podcast, second_parent)
        self.assertEqual(episode.season, season)

    def test_invalid_content_graph_writes_are_rejected(self):
        standalone = Podcast.objects.create(title="Standalone is not a season parent")
        child = Podcast.objects.create(
            title="Existing malformed child",
            structure=BasePost.Structure.CHILD,
        )

        invalid_child = PodcastSerializer(
            data={
                "title": "Invalid child",
                "structure": BasePost.Structure.CHILD,
                "parent": str(standalone.pk),
            }
        )
        invalid_root = PodcastSerializer(
            data={
                "title": "Invalid root",
                "structure": BasePost.Structure.STANDALONE,
                "parent": str(standalone.pk),
            }
        )
        invalid_season = SeasonSerializer(
            data={
                "podcast": str(child.pk),
                "title": "Invalid season",
                "position": 1,
            }
        )

        self.assertFalse(invalid_child.is_valid())
        self.assertFalse(invalid_root.is_valid())
        self.assertFalse(invalid_season.is_valid())

    def test_materialized_podcast_structure_cannot_be_reinterpreted(self):
        parent = Podcast.objects.create(
            title="Materialized parent",
            structure=BasePost.Structure.PARENT,
        )
        child_serializer = PodcastSerializer(
            data={
                "title": "Materialized child",
                "structure": BasePost.Structure.CHILD,
                "parent": str(parent.pk),
            }
        )
        self.assertTrue(child_serializer.is_valid(), child_serializer.errors)
        child = child_serializer.save()

        flatten_child = PodcastSerializer(
            child,
            data={
                "structure": BasePost.Structure.STANDALONE,
                "parent": None,
            },
            partial=True,
        )
        flatten_parent = PodcastSerializer(
            parent,
            data={"structure": BasePost.Structure.STANDALONE},
            partial=True,
        )

        self.assertFalse(flatten_child.is_valid())
        self.assertIn("structure", flatten_child.errors)
        self.assertFalse(flatten_parent.is_valid())
        self.assertIn("structure", flatten_parent.errors)

    def test_legacy_season_allocates_number_independently_from_position(self):
        parent = Podcast.objects.create(
            title="Sparse numbered parent",
            structure=BasePost.Structure.PARENT,
        )
        Season.objects.create(
            podcast=parent,
            title="Existing explicit season",
            position=1,
            number=2,
        )
        child_serializer = PodcastSerializer(
            data={
                "title": "Compatible legacy season",
                "structure": BasePost.Structure.CHILD,
                "parent": str(parent.pk),
            }
        )

        self.assertTrue(child_serializer.is_valid(), child_serializer.errors)
        child = child_serializer.save()
        season = Season.objects.get(legacy_podcast=child)

        self.assertEqual(season.position, 2)
        self.assertEqual(season.number, 3)


class EpisodeDashboardPublicationCompatibilityTests(TestCase):
    def setUp(self):
        self.podcast = Podcast.objects.create(title="Dashboard publication")
        self.free = Plan.objects.create(name="Dashboard free", tier=Plan.Level.FREE)
        self.fan = Plan.objects.create(name="Dashboard fan", tier=Plan.Level.FAN)
        self.pro = Plan.objects.create(name="Dashboard pro", tier=Plan.Level.PRO)
        self.free_category = Category.objects.create(name="Dashboard free gate", tier=self.free)
        self.category = Category.objects.create(name="Dashboard gate", tier=self.fan)
        self.release_at = timezone.now() + datetime.timedelta(hours=1)

    def test_legacy_dashboard_write_populates_canonical_fields(self):
        serializer = EpisodeSerializer(
            data={
                "podcast": str(self.podcast.pk),
                "title": "Legacy dashboard episode",
                "public_release_date": self.release_at.isoformat(),
                "exclusive": True,
                "categories": [str(self.category.pk)],
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        episode = serializer.save()

        self.assertEqual(episode.status, Episode.PublicationStatus.PUBLISHED)
        self.assertEqual(episode.visibility, Episode.Visibility.PLAN)
        self.assertEqual(episode.premium_available_at, self.release_at)
        self.assertIsNone(episode.public_available_at)
        self.assertEqual(episode.required_plan, self.fan)

    def test_canonical_dashboard_write_keeps_a_legacy_projection(self):
        serializer = EpisodeSerializer(
            data={
                "podcast": str(self.podcast.pk),
                "title": "Canonical dashboard episode",
                "status": Episode.PublicationStatus.PUBLISHED,
                "visibility": Episode.Visibility.PLAN,
                "premium_available_at": self.release_at.isoformat(),
                "required_plan": str(self.fan.pk),
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        episode = serializer.save()

        self.assertTrue(episode.exclusive)
        self.assertEqual(episode.public_release_date, self.release_at)

    def test_taxonomy_only_update_does_not_rewrite_canonical_access(self):
        episode = Episode.objects.create(
            podcast=self.podcast,
            title="Canonical policy survives taxonomy edits",
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PUBLIC,
            premium_available_at=self.release_at,
            public_available_at=self.release_at,
        )

        serializer = EpisodeSerializer(
            instance=episode,
            data={"categories": [str(self.category.pk)]},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.visibility, Episode.Visibility.PUBLIC)
        self.assertIsNone(updated.required_plan)
        self.assertEqual(updated.public_available_at, self.release_at)

    def test_early_access_only_update_does_not_rewrite_canonical_access(self):
        episode = Episode.objects.create(
            podcast=self.podcast,
            title="Canonical policy survives early-access edits",
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PUBLIC,
            premium_available_at=self.release_at,
            public_available_at=self.release_at,
        )

        serializer = EpisodeSerializer(
            instance=episode,
            data={"early_access_hours": 6},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.visibility, Episode.Visibility.PUBLIC)
        self.assertIsNone(updated.required_plan)
        self.assertEqual(updated.public_available_at, self.release_at)

    def test_legacy_exclusive_free_category_uses_lowest_paid_plan(self):
        serializer = EpisodeSerializer(
            data={
                "podcast": str(self.podcast.pk),
                "title": "Free-tagged legacy exclusive episode",
                "public_release_date": self.release_at.isoformat(),
                "exclusive": True,
                "categories": [str(self.free_category.pk)],
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        episode = serializer.save()

        self.assertEqual(episode.visibility, Episode.Visibility.PLAN)
        self.assertIsNone(episode.public_available_at)
        self.assertEqual(episode.required_plan, self.fan)

    def test_unrepresentable_canonical_window_projects_fail_closed(self):
        serializer = EpisodeSerializer(
            data={
                "podcast": str(self.podcast.pk),
                "title": "Premium now, public date unknown",
                "status": Episode.PublicationStatus.PUBLISHED,
                "visibility": Episode.Visibility.PUBLIC,
                "premium_available_at": self.release_at.isoformat(),
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        episode = serializer.save()
        self.assertTrue(episode.exclusive)
        self.assertEqual(episode.public_release_date, self.release_at)

        legacy_round_trip = EpisodeSerializer(
            instance=episode,
            data={
                "public_release_date": episode.public_release_date.isoformat(),
                "exclusive": episode.exclusive,
            },
            partial=True,
        )

        self.assertTrue(legacy_round_trip.is_valid(), legacy_round_trip.errors)
        round_tripped = legacy_round_trip.save()

        self.assertEqual(round_tripped.visibility, Episode.Visibility.PLAN)
        self.assertIsNone(round_tripped.public_available_at)
        self.assertEqual(round_tripped.required_plan, self.fan)

    def test_legacy_release_only_update_preserves_explicit_required_plan(self):
        episode = Episode.objects.create(
            podcast=self.podcast,
            title="Explicit pro policy",
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PLAN,
            required_plan=self.pro,
            premium_available_at=self.release_at,
        )
        later_release = self.release_at + datetime.timedelta(hours=1)
        serializer = EpisodeSerializer(
            instance=episode,
            data={
                "public_release_date": later_release.isoformat(),
                "exclusive": True,
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.visibility, Episode.Visibility.PLAN)
        self.assertEqual(updated.required_plan, self.pro)
        self.assertEqual(updated.premium_available_at, later_release)

    def test_legacy_round_trip_cannot_widen_entitlement_visibility(self):
        serializer = EpisodeSerializer(
            data={
                "podcast": str(self.podcast.pk),
                "title": "Entitlement-only episode",
                "status": Episode.PublicationStatus.PUBLISHED,
                "visibility": Episode.Visibility.ENTITLEMENT,
                "premium_available_at": self.release_at.isoformat(),
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        episode = serializer.save()
        legacy_round_trip = EpisodeSerializer(
            instance=episode,
            data={
                "public_release_date": episode.public_release_date.isoformat(),
                "exclusive": episode.exclusive,
            },
            partial=True,
        )

        self.assertTrue(legacy_round_trip.is_valid(), legacy_round_trip.errors)
        round_tripped = legacy_round_trip.save()

        self.assertEqual(round_tripped.visibility, Episode.Visibility.ENTITLEMENT)
        self.assertIsNone(round_tripped.required_plan)
        self.assertIsNone(round_tripped.public_available_at)

    def test_repeating_current_podcast_does_not_detach_existing_season(self):
        season = Season.objects.create(
            podcast=self.podcast,
            title="Preserved season",
            position=1,
        )
        episode = Episode.objects.create(
            podcast=self.podcast,
            season=season,
            title="Season ownership survives",
        )
        serializer = EpisodeSerializer(
            episode,
            data={
                "podcast": str(self.podcast.pk),
                "title": "Season ownership still survives",
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.season, season)
