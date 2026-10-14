from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from utils.utils import generate_code

from apps.region.leagues.clubs.models import Team
from apps.region.leagues.models import League
from apps.region.models import Country, Region


class SportsCodeTests(TestCase):
    def test_region_without_code_creates_once_and_keeps_public_identifiers(self):
        with patch("apps.region.receivers.generate_code", return_value="1234"):
            region = Region.objects.create(name="Europe")
        identity = (region.pk, region.slug, region.code)
        region.name = "European region"
        region.save()
        region.refresh_from_db()
        self.assertEqual((region.pk, region.slug, region.code), identity)
        self.assertEqual(region.code, 1234)

    def test_country_code_is_assigned_in_original_insert(self):
        region = Region.objects.create(name="Europe", code=1111)
        with (
            patch("apps.region.receivers.generate_code", return_value="2222"),
            CaptureQueriesContext(connection) as queries,
        ):
            country = Country.objects.create(name="England", region=region)
        country.refresh_from_db()
        self.assertEqual(country.code, 2222)
        self.assertFalse(any(q["sql"].startswith("UPDATE") for q in queries))
        self.assertEqual(country.region_id, region.pk)

    def test_explicit_zero_codes_are_preserved_for_all_structured_entities(self):
        region = Region.objects.create(name="Europe", code=0)
        country = Country.objects.create(name="England", region=region, code=0)
        league = League.objects.create(name="Premier League", region=country, code=0)
        team = Team.objects.create(name="Arsenal", league=league, code=0)
        for instance in (region, country, league, team):
            with self.subTest(model=type(instance).__name__):
                instance.refresh_from_db()
                self.assertEqual(instance.code, 0)

    def test_raw_fixture_saves_do_not_invent_codes_or_change_slugs(self):
        region = Region(name="Europe", slug="historic-europe", timestamp=timezone.now())
        country = Country(
            name="England", region=region, slug="historic-england", timestamp=timezone.now()
        )
        league = League(
            name="Premier League", region=country, slug="historic-league", timestamp=timezone.now()
        )
        team = Team(name="Arsenal", league=league, slug="historic-team", timestamp=timezone.now())
        for instance in (region, country, league, team):
            with self.subTest(model=type(instance).__name__):
                slug = instance.slug
                instance.save_base(raw=True)
                instance.refresh_from_db()
                self.assertIsNone(instance.code)
                self.assertEqual(instance.slug, slug)

    def test_collision_retries_return_the_unused_candidate(self):
        Region.objects.create(name="Existing", code=1111)
        with patch("utils.utils.random.choice", side_effect=list("11112222")):
            region = Region.objects.create(name="New region")
        self.assertEqual(region.code, 2222)

    def test_code_exhaustion_is_bounded_and_does_not_create_a_region(self):
        Region.objects.create(name="Existing", code=1111)
        with (
            patch("utils.utils.random.choice", return_value="1") as random_digit,
            self.assertRaisesMessage(ValidationError, "Could not allocate an unused code"),
        ):
            Region.objects.create(name="No available candidate")
        self.assertEqual(random_digit.call_count, 400)
        self.assertEqual(Region.objects.count(), 1)

    def test_generation_without_a_model_remains_compatible(self):
        with patch("utils.utils.random.choice", return_value="4"):
            self.assertEqual(generate_code(6), "444444")
