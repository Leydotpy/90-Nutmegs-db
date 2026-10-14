from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class CategoryTaxonomyMigrationTests(TransactionTestCase):
    migrate_from = [
        ("category", "0002_initial"),
        ("podcasts", "0003_canonical_podcast_seasons"),
    ]
    migrate_to = [("category", "0003_alter_category_slug_alter_category_tier")]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        self.old_apps = executor.loader.project_state(self.migrate_from).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_expansion_preserves_identifiers_links_and_backfilled_episode_access(self):
        OldPlan = self.old_apps.get_model("memberships", "Plan")
        OldCategory = self.old_apps.get_model("category", "Category")
        OldPodcast = self.old_apps.get_model("podcasts", "Podcast")
        OldEpisode = self.old_apps.get_model("podcasts", "Episode")
        historical_plan = OldPlan.objects.create(name="Historical category plan", tier=1)
        explicit_plan = OldPlan.objects.create(name="Canonical episode plan", tier=2)
        category = OldCategory.objects.create(
            name="Football analysis",
            slug="existing-category-url-including-legacy-tier",
            tier=historical_plan,
        )
        podcast = OldPodcast.objects.create(title="Existing podcast", slug="existing-show")
        episode = OldEpisode.objects.create(
            podcast=podcast,
            title="Existing episode",
            visibility="plan",
            required_plan=explicit_plan,
        )
        podcast.categories.add(category)
        episode.categories.add(category)

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        new_apps = executor.loader.project_state(self.migrate_to).apps
        NewCategory = new_apps.get_model("category", "Category")
        NewPodcast = new_apps.get_model("podcasts", "Podcast")
        NewEpisode = new_apps.get_model("podcasts", "Episode")
        migrated_category = NewCategory.objects.get(pk=category.pk)
        migrated_podcast = NewPodcast.objects.get(pk=podcast.pk)
        migrated_episode = NewEpisode.objects.get(pk=episode.pk)

        self.assertEqual(migrated_category.slug, category.slug)
        self.assertEqual(migrated_category.tier_id, historical_plan.pk)
        self.assertEqual(
            list(migrated_podcast.categories.values_list("pk", flat=True)), [category.pk]
        )
        self.assertEqual(
            list(migrated_episode.categories.values_list("pk", flat=True)), [category.pk]
        )
        self.assertEqual(migrated_podcast.slug, podcast.slug)
        self.assertEqual(migrated_episode.slug, episode.slug)
        self.assertEqual(migrated_episode.required_plan_id, explicit_plan.pk)
        self.assertEqual(migrated_episode.visibility, "plan")

        tierless_category = NewCategory.objects.create(name="Fresh football topic")
        self.assertIsNone(tierless_category.tier_id)
        self.assertTrue(tierless_category.slug.startswith("fresh-football-topic-"))

        # Null tiers intentionally block an unprepared return to the old NOT NULL
        # schema. Rollback requires explicit data reconciliation, not guessed plans.
