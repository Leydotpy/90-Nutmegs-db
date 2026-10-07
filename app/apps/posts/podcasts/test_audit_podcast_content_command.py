import datetime
import json
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from apps.posts.models import BasePost
from apps.posts.podcasts.models import Episode, Podcast, Season


class AuditPodcastContentCommandTests(TestCase):
    def setUp(self):
        self.open_at = timezone.now() - datetime.timedelta(hours=1)

    def create_published_podcast(self, title, **kwargs):
        return Podcast.objects.create(
            title=title,
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=self.open_at,
            **kwargs,
        )

    def run_command(self, **options):
        stdout = StringIO()
        call_command("audit_podcast_content", stdout=stdout, **options)
        return json.loads(stdout.getvalue())

    def test_clean_canonical_content_reports_zero_drift(self):
        podcast = self.create_published_podcast("Canonical show")
        season = Season.objects.create(
            podcast=podcast,
            title="Canonical season",
            position=1,
            published_at=self.open_at,
        )
        Episode.objects.create(
            podcast=podcast,
            season=season,
            title="Canonical episode",
            status=Episode.PublicationStatus.PUBLISHED,
        )
        draft = Podcast.objects.create(title="Draft show")
        Episode.objects.create(podcast=draft, title="Draft episode")

        payload = self.run_command(fail_on_drift=True)

        self.assertFalse(payload["drift_detected"])
        self.assertEqual(payload["drift_count"], 0)
        self.assertEqual(set(payload["counts"].values()), {0})

    def test_command_reports_each_canonical_content_drift_category(self):
        canonical = self.create_published_podcast("Canonical show")
        parent = self.create_published_podcast(
            "Legacy parent",
            structure=BasePost.Structure.PARENT,
        )
        missing_season_child = self.create_published_podcast(
            "Legacy child without season",
            structure=BasePost.Structure.CHILD,
            parent=parent,
        )
        mismatched_season_child = self.create_published_podcast(
            "Legacy child with wrong season",
            structure=BasePost.Structure.CHILD,
            parent=parent,
        )
        wrong_parent = self.create_published_podcast("Wrong canonical parent")
        wrong_season = Season.objects.create(
            podcast=wrong_parent,
            legacy_podcast=mismatched_season_child,
            title="Mismatched legacy season",
            position=1,
        )

        child_owned_episode = Episode.objects.create(
            podcast=missing_season_child,
            title="Still child owned",
        )
        mismatched_episode = Episode.objects.create(
            podcast=canonical,
            title="Mismatched season ownership",
        )
        Episode.objects.filter(pk=mismatched_episode.pk).update(season=wrong_season)

        missing_publication_time = Podcast.objects.create(
            title="Published without publication time",
            status=Podcast.PublicationStatus.PUBLISHED,
        )
        future_podcast = Podcast.objects.create(
            title="Future podcast",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now() + datetime.timedelta(days=1),
        )
        draft_podcast = Podcast.objects.create(title="Draft podcast")
        for podcast, title in (
            (missing_publication_time, "Missing-time episode"),
            (future_podcast, "Future-show episode"),
            (draft_podcast, "Draft-show episode"),
        ):
            Episode.objects.create(
                podcast=podcast,
                title=title,
                status=Episode.PublicationStatus.PUBLISHED,
            )

        payload = self.run_command()

        self.assertTrue(payload["drift_detected"])
        self.assertEqual(
            payload["counts"],
            {
                "episode_season_podcast_mismatches": 1,
                "episodes_owned_by_legacy_child": 1,
                "legacy_children_missing_explicit_season": 1,
                "legacy_children_missing_parent": 0,
                "legacy_children_with_mismatched_explicit_season": 1,
                "legacy_children_with_invalid_parent": 0,
                "nonchild_podcasts_with_parent": 0,
                "published_episodes_with_undiscoverable_podcast": 3,
                "published_podcasts_missing_published_at": 1,
            },
        )
        self.assertEqual(payload["drift_count"], 8)

        child_owned_episode.refresh_from_db()
        mismatched_episode.refresh_from_db()
        self.assertEqual(child_owned_episode.podcast, missing_season_child)
        self.assertEqual(mismatched_episode.season, wrong_season)

    def test_fail_on_drift_raises_after_emitting_json_report(self):
        Podcast.objects.create(
            title="Published without timestamp",
            status=Podcast.PublicationStatus.PUBLISHED,
        )
        stdout = StringIO()

        with self.assertRaisesMessage(
            CommandError,
            "Podcast canonical-content drift detected (1 finding).",
        ):
            call_command(
                "audit_podcast_content",
                fail_on_drift=True,
                stdout=stdout,
            )

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["drift_detected"])
        self.assertEqual(payload["drift_count"], 1)

    def test_invalid_legacy_graph_shapes_are_reported(self):
        standalone_parent = self.create_published_podcast("Not a parent")
        Podcast.objects.create(
            title="Child of standalone",
            structure=BasePost.Structure.CHILD,
            parent=standalone_parent,
        )
        Podcast.objects.create(
            title="Orphan child",
            structure=BasePost.Structure.CHILD,
        )
        Podcast.objects.create(
            title="Malformed standalone child",
            structure=BasePost.Structure.STANDALONE,
            parent=standalone_parent,
        )

        payload = self.run_command()

        self.assertEqual(payload["counts"]["legacy_children_missing_explicit_season"], 2)
        self.assertEqual(payload["counts"]["legacy_children_missing_parent"], 1)
        self.assertEqual(payload["counts"]["legacy_children_with_invalid_parent"], 1)
        self.assertEqual(payload["counts"]["nonchild_podcasts_with_parent"], 1)
