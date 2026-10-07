import datetime
import importlib
from types import SimpleNamespace

from django.apps import apps as django_apps
from django.db import connection
from django.test import TransactionTestCase
from django.utils import timezone

from apps.category.models import Category
from apps.memberships.models import Plan
from apps.posts.podcasts.models import Episode, Podcast


class EpisodePublicationBackfillTests(TransactionTestCase):
    def test_backfill_is_deterministic_and_fail_closed_for_undated_content(self):
        now = timezone.now().replace(microsecond=0)
        free = Plan.objects.create(name="Free migration", tier=Plan.Level.FREE)
        fan = Plan.objects.create(name="Fan migration", tier=Plan.Level.FAN)
        pro = Plan.objects.create(name="Pro migration", tier=Plan.Level.PRO)
        free_category = Category.objects.create(name="Free legacy gate", tier=free)
        podcast_category = Category.objects.create(name="Fan gate", tier=fan)
        episode_category = Category.objects.create(name="Pro gate", tier=pro)
        podcast = Podcast.objects.create(title="Migration podcast")
        podcast.categories.add(podcast_category)

        public_episode = Episode.objects.create(
            podcast=podcast,
            title="Public legacy episode",
            public_release_date=now - datetime.timedelta(hours=1),
        )
        public_episode.categories.add(episode_category)
        exclusive_episode = Episode.objects.create(
            podcast=Podcast.objects.create(title="Exclusive migration podcast"),
            title="Exclusive legacy episode",
            public_release_date=now + datetime.timedelta(hours=2),
            exclusive=True,
        )
        exclusive_free_episode = Episode.objects.create(
            podcast=Podcast.objects.create(title="Free-tagged exclusive migration podcast"),
            title="Free-tagged exclusive legacy episode",
            public_release_date=now - datetime.timedelta(minutes=30),
            exclusive=True,
        )
        exclusive_free_episode.categories.add(free_category)
        undated_episode = Episode.objects.create(
            podcast=podcast,
            title="Undated legacy episode",
        )

        migration = importlib.import_module(
            "apps.posts.podcasts.migrations.0002_episode_publication_access"
        )
        schema_editor = SimpleNamespace(connection=connection)
        migration.backfill_episode_publication_access(django_apps, schema_editor)
        migration.backfill_episode_publication_access(django_apps, schema_editor)

        public_episode.refresh_from_db()
        exclusive_episode.refresh_from_db()
        exclusive_free_episode.refresh_from_db()
        undated_episode.refresh_from_db()

        self.assertEqual(public_episode.status, Episode.PublicationStatus.PUBLISHED)
        self.assertEqual(public_episode.visibility, Episode.Visibility.PUBLIC)
        self.assertEqual(public_episode.premium_available_at, public_episode.public_release_date)
        self.assertEqual(public_episode.public_available_at, public_episode.public_release_date)
        self.assertEqual(public_episode.required_plan, pro)

        self.assertEqual(exclusive_episode.status, Episode.PublicationStatus.PUBLISHED)
        self.assertEqual(exclusive_episode.visibility, Episode.Visibility.PLAN)
        self.assertEqual(
            exclusive_episode.premium_available_at,
            exclusive_episode.public_release_date,
        )
        self.assertIsNone(exclusive_episode.public_available_at)
        self.assertEqual(exclusive_episode.required_plan, fan)

        self.assertEqual(exclusive_free_episode.visibility, Episode.Visibility.PLAN)
        self.assertIsNone(exclusive_free_episode.public_available_at)
        self.assertEqual(exclusive_free_episode.required_plan, fan)

        self.assertEqual(undated_episode.status, Episode.PublicationStatus.DRAFT)
        self.assertEqual(undated_episode.visibility, Episode.Visibility.PUBLIC)
        self.assertIsNone(undated_episode.premium_available_at)
        self.assertIsNone(undated_episode.public_available_at)
        self.assertEqual(undated_episode.required_plan, fan)
