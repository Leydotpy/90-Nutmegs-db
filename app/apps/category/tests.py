from api.rest.dashboard.apps.category.serializers import CategorySerializer
from django.contrib import admin
from django.test import RequestFactory, TestCase

from apps.category.models import Category
from apps.memberships.models import Plan
from apps.posts.podcasts.models import Episode, Podcast


class CategoryTaxonomyTests(TestCase):
    def test_dashboard_creates_category_without_a_commercial_plan(self):
        serializer = CategorySerializer(data={"name": "Football tactics"})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        category = serializer.save()

        self.assertIsNone(category.tier_id)
        self.assertTrue(category.slug.startswith("football-tactics-"))
        self.assertEqual(Plan.objects.count(), 0)
        self.assertIsNone(CategorySerializer(category).data["tier"])

    def test_editing_historical_category_preserves_public_identifier_and_slug(self):
        plan = Plan.objects.create(name="Historical paid tier", tier=Plan.Level.PRO)
        category = Category.objects.create(
            name="Historical category",
            slug="historical-public-category-slug",
            tier=plan,
        )
        category_id = category.pk

        serializer = CategorySerializer(
            category,
            data={"name": "Renamed football topic", "description": "Updated topic"},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        category.refresh_from_db()

        self.assertEqual(category.pk, category_id)
        self.assertEqual(category.slug, "historical-public-category-slug")
        self.assertEqual(category.name, "Renamed football topic")
        self.assertEqual(category.tier, plan)

    def test_deleting_historical_plan_preserves_taxonomy_links_and_explicit_access(self):
        historical_plan = Plan.objects.create(name="Historical tier", tier=Plan.Level.FAN)
        explicit_plan = Plan.objects.create(name="Explicit access", tier=Plan.Level.PRO)
        category = Category.objects.create(name="Match analysis", tier=historical_plan)
        podcast = Podcast.objects.create(title="Analysis show")
        episode = Episode.objects.create(
            podcast=podcast,
            title="Analysis episode",
            visibility=Episode.Visibility.PLAN,
            required_plan=explicit_plan,
        )
        podcast.categories.add(category)
        episode.categories.add(category)
        category_id, category_slug = category.pk, category.slug

        historical_plan.delete()

        category.refresh_from_db()
        episode.refresh_from_db()
        self.assertEqual(category.pk, category_id)
        self.assertEqual(category.slug, category_slug)
        self.assertIsNone(category.tier_id)
        self.assertEqual(list(podcast.categories.all()), [category])
        self.assertEqual(list(episode.categories.all()), [category])
        self.assertEqual(episode.required_plan, explicit_plan)
        self.assertEqual(episode.visibility, Episode.Visibility.PLAN)

    def test_dashboard_and_admin_keep_historical_tier_read_only(self):
        original_plan = Plan.objects.create(name="Original tier", tier=Plan.Level.FAN)
        replacement_plan = Plan.objects.create(name="Replacement tier", tier=Plan.Level.PRO)
        category = Category.objects.create(name="Existing topic", tier=original_plan)

        update = CategorySerializer(
            category,
            data={"name": "Edited topic", "tier": str(replacement_plan.pk)},
            partial=True,
        )
        self.assertTrue(update.is_valid(), update.errors)
        update.save()
        category.refresh_from_db()
        self.assertEqual(category.tier, original_plan)

        create = CategorySerializer(data={"name": "New topic", "tier": str(replacement_plan.pk)})
        self.assertTrue(create.is_valid(), create.errors)
        self.assertIsNone(create.save().tier_id)

        category_admin = admin.site._registry[Category]
        request = RequestFactory().get("/admin/category/category/")
        self.assertIn("tier", category_admin.get_readonly_fields(request, category))
        self.assertNotIn("tier", category_admin.get_form(request, category).base_fields)
