import datetime
import importlib
from types import SimpleNamespace

from django.apps import apps as django_apps
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.posts.models import BasePost
from apps.posts.podcasts.models import Episode, Podcast, Season


class CanonicalContentBackfillTests(TransactionTestCase):
    def test_child_podcast_becomes_one_explicit_season_without_data_loss(self):
        release_at = timezone.now().replace(microsecond=0) - datetime.timedelta(hours=1)
        parent = Podcast.objects.create(
            title="Legacy parent show",
            structure=BasePost.Structure.PARENT,
        )
        child = Podcast.objects.create(
            title="Legacy season one",
            structure=BasePost.Structure.CHILD,
            parent=parent,
        )
        episode = Episode.objects.create(
            podcast=child,
            title="Legacy season episode",
            status=Episode.PublicationStatus.PUBLISHED,
            public_release_date=release_at,
            premium_available_at=release_at,
            public_available_at=release_at,
        )

        migration = importlib.import_module(
            "apps.posts.podcasts.migrations.0003_canonical_podcast_seasons"
        )
        schema_editor = SimpleNamespace(connection=connection)
        migration.backfill_canonical_content(django_apps, schema_editor)
        migration.backfill_canonical_content(django_apps, schema_editor)

        parent.refresh_from_db()
        child.refresh_from_db()
        episode.refresh_from_db()
        season = Season.objects.get(legacy_podcast=child)

        self.assertEqual(Season.objects.filter(legacy_podcast=child).count(), 1)
        self.assertEqual(season.podcast, parent)
        self.assertEqual(season.number, 1)
        self.assertEqual(season.position, 1)
        self.assertEqual(season.title, child.title)
        self.assertEqual(season.slug, child.slug)
        self.assertEqual(episode.podcast, parent)
        self.assertEqual(episode.season, season)
        self.assertEqual(episode.published_at, release_at)
        self.assertEqual(parent.status, Podcast.PublicationStatus.PUBLISHED)
        self.assertEqual(child.status, Podcast.PublicationStatus.PUBLISHED)
        self.assertEqual(list(child.get_discoverable_episodes()), [episode])

        migration.restore_legacy_episode_ownership(django_apps, schema_editor)
        episode.refresh_from_db()
        self.assertEqual(episode.podcast, child)
        self.assertIsNone(episode.season)


class CanonicalContentHistoricalMigrationTests(TransactionTestCase):
    migrate_from = [("podcasts", "0002_episode_publication_access")]
    migrate_to = [("podcasts", "0003_canonical_podcast_seasons")]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        self.old_apps = executor.loader.project_state(self.migrate_from).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_duplicate_slugs_are_repaired_before_constraints_and_seasons_backfill(self):
        OldPodcast = self.old_apps.get_model("podcasts", "Podcast")
        OldEpisode = self.old_apps.get_model("podcasts", "Episode")
        shared_episode_slug = "f8b86513-420e-40b5-9f47-44a074a30d1a"
        release_at = timezone.now().replace(microsecond=0) - datetime.timedelta(hours=1)
        parent = OldPodcast.objects.create(
            title="Historical parent",
            slug="duplicate-show-slug",
            structure="PARENT",
        )
        children = [
            OldPodcast.objects.create(
                title=f"Historical season {number}",
                slug="duplicate-show-slug",
                structure="CHILD",
                parent=parent,
            )
            for number in (1, 2)
        ]
        episodes = [
            OldEpisode.objects.create(
                podcast=child,
                title=f"Historical episode {number}",
                slug=shared_episode_slug,
                public_release_date=release_at,
                status="published",
                visibility="public",
                premium_available_at=release_at,
                public_available_at=release_at,
            )
            for number, child in enumerate(children, start=1)
        ]

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        new_apps = executor.loader.project_state(self.migrate_to).apps
        NewPodcast = new_apps.get_model("podcasts", "Podcast")
        NewSeason = new_apps.get_model("podcasts", "Season")
        NewEpisode = new_apps.get_model("podcasts", "Episode")

        migrated_parent = NewPodcast.objects.get(pk=parent.pk)
        migrated_children = list(
            NewPodcast.objects.filter(pk__in=[child.pk for child in children]).order_by(
                "timestamp", "pk"
            )
        )
        migrated_seasons = list(NewSeason.objects.filter(podcast_id=parent.pk).order_by("position"))
        migrated_episodes = list(
            NewEpisode.objects.filter(pk__in=[episode.pk for episode in episodes]).order_by(
                "timestamp", "pk"
            )
        )

        podcast_slugs = {
            migrated_parent.slug,
            *(child.slug for child in migrated_children),
        }
        self.assertEqual(len(podcast_slugs), 3)
        self.assertEqual(migrated_parent.slug, "duplicate-show-slug")
        self.assertEqual([season.position for season in migrated_seasons], [1, 2])
        self.assertEqual(
            [season.legacy_podcast_id for season in migrated_seasons],
            [child.pk for child in migrated_children],
        )
        self.assertEqual(len({season.slug for season in migrated_seasons}), 2)
        self.assertEqual(len({episode.slug for episode in migrated_episodes}), 2)
        self.assertTrue(
            all(episode.podcast_id == migrated_parent.pk for episode in migrated_episodes)
        )
        self.assertTrue(all(episode.season_id is not None for episode in migrated_episodes))

    def test_invalid_child_parent_graph_is_left_for_explicit_reconciliation(self):
        OldPodcast = self.old_apps.get_model("podcasts", "Podcast")
        OldEpisode = self.old_apps.get_model("podcasts", "Episode")
        standalone = OldPodcast.objects.create(
            title="Historical standalone",
            structure="STANDALONE",
        )
        invalid_child = OldPodcast.objects.create(
            title="Historical invalid child",
            structure="CHILD",
            parent=standalone,
        )
        episode = OldEpisode.objects.create(
            podcast=invalid_child,
            title="Historical unmapped episode",
            status="published",
            visibility="public",
        )

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        new_apps = executor.loader.project_state(self.migrate_to).apps
        NewSeason = new_apps.get_model("podcasts", "Season")
        NewEpisode = new_apps.get_model("podcasts", "Episode")
        migrated_episode = NewEpisode.objects.get(pk=episode.pk)

        self.assertFalse(NewSeason.objects.filter(legacy_podcast_id=invalid_child.pk).exists())
        self.assertEqual(migrated_episode.podcast_id, invalid_child.pk)
        self.assertIsNone(migrated_episode.season_id)

    def test_generated_slug_does_not_displace_a_later_legitimate_slug(self):
        OldPodcast = self.old_apps.get_model("podcasts", "Podcast")
        blank = OldPodcast.objects.create(
            title="Historical blank slug",
            slug=None,
        )
        legitimate_slug = f"podcast-{str(blank.pk).replace('-', '').lower()}"
        legitimate = OldPodcast.objects.create(
            title="Historical legitimate generated-looking slug",
            slug=legitimate_slug,
        )
        base_time = timezone.now().replace(microsecond=0) - datetime.timedelta(days=1)
        OldPodcast.objects.filter(pk=blank.pk).update(timestamp=base_time)
        OldPodcast.objects.filter(pk=legitimate.pk).update(
            timestamp=base_time + datetime.timedelta(seconds=1)
        )

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        new_apps = executor.loader.project_state(self.migrate_to).apps
        NewPodcast = new_apps.get_model("podcasts", "Podcast")
        migrated_blank = NewPodcast.objects.get(pk=blank.pk)
        migrated_legitimate = NewPodcast.objects.get(pk=legitimate.pk)

        self.assertEqual(migrated_legitimate.slug, legitimate_slug)
        self.assertNotEqual(migrated_blank.slug, legitimate_slug)
        self.assertTrue(migrated_blank.slug.startswith(f"{legitimate_slug}-"))

    def test_schema_can_reverse_and_reapply_with_episode_ownership_restored(self):
        OldPodcast = self.old_apps.get_model("podcasts", "Podcast")
        OldEpisode = self.old_apps.get_model("podcasts", "Episode")
        parent = OldPodcast.objects.create(
            title="Rollback parent",
            structure="PARENT",
        )
        child = OldPodcast.objects.create(
            title="Rollback child",
            structure="CHILD",
            parent=parent,
        )
        episode = OldEpisode.objects.create(
            podcast=child,
            title="Rollback episode",
            status="published",
            visibility="public",
        )
        parent_id = parent.pk
        child_id = child.pk
        episode_id = episode.pk

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        migrated_apps = executor.loader.project_state(self.migrate_to).apps
        MigratedEpisode = migrated_apps.get_model("podcasts", "Episode")
        migrated_episode = MigratedEpisode.objects.get(pk=episode_id)
        self.assertEqual(migrated_episode.podcast_id, parent_id)
        self.assertIsNotNone(migrated_episode.season_id)

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        reverted_apps = executor.loader.project_state(self.migrate_from).apps
        RevertedEpisode = reverted_apps.get_model("podcasts", "Episode")
        reverted_episode = RevertedEpisode.objects.get(pk=episode_id)
        self.assertEqual(reverted_episode.podcast_id, child_id)

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        reapplied_apps = executor.loader.project_state(self.migrate_to).apps
        ReappliedEpisode = reapplied_apps.get_model("podcasts", "Episode")
        ReappliedSeason = reapplied_apps.get_model("podcasts", "Season")
        reapplied_episode = ReappliedEpisode.objects.get(pk=episode_id)
        self.assertEqual(reapplied_episode.podcast_id, parent_id)
        self.assertTrue(
            ReappliedSeason.objects.filter(pk=reapplied_episode.season_id).exists()
        )


class CanonicalContentModelTests(TestCase):
    def test_new_podcasts_fail_closed_until_explicitly_published(self):
        now = timezone.now()
        draft = Podcast.objects.create(title="Draft canonical show")
        published = Podcast.objects.create(
            title="Published canonical show",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=now - datetime.timedelta(minutes=1),
        )
        scheduled = Podcast.objects.create(
            title="Scheduled canonical show",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=now + datetime.timedelta(hours=1),
        )

        self.assertEqual(list(Podcast.objects.discoverable(now=now)), [published])
        self.assertNotIn(draft, Podcast.objects.published(now=now))
        self.assertNotIn(scheduled, Podcast.objects.published(now=now))

    def test_episode_rejects_a_season_owned_by_another_podcast(self):
        first = Podcast.objects.create(title="First show")
        second = Podcast.objects.create(title="Second show")
        season = Season.objects.create(
            podcast=first,
            title="First season",
            position=1,
        )

        with self.assertRaisesMessage(
            ValueError,
            "episode.podcast must match episode.season.podcast",
        ):
            Episode.objects.create(
                podcast=second,
                season=season,
                title="Mismatched episode",
            )
