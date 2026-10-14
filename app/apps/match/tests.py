from datetime import date
from unittest.mock import patch

from api.rest.dashboard.apps.match.serializers import MatchSerializer
from django.db.models.query import QuerySet
from django.test import TestCase
from django.utils import timezone

from apps.match.models import Event, Match, Possession, TeamPossession
from apps.match.services import initialize_match_event
from apps.match.signals import create_match_event
from apps.persons.models import Player
from apps.posts.podcasts.models import Episode, Podcast
from apps.region.leagues.clubs.models import Team
from apps.region.leagues.models import Campaign, League
from apps.region.models import Country, Region


class MatchMetadataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.region = Region.objects.create(name="Europe", code=1)
        cls.country = Country.objects.create(name="England", region=cls.region, code=1)
        cls.league = League.objects.create(name="Premier League", region=cls.country, code=1)
        cls.home = Team.objects.create(name="Arsenal", league=cls.league, code=1)
        cls.away = Team.objects.create(name="Everton", league=cls.league, code=2)
        cls.campaign = Campaign.objects.create(start=date(2026, 8, 1), end=date(2027, 5, 31))

    def match_data(self):
        return {
            "home_team": self.home,
            "away_team": self.away,
            "competition": self.league,
            "campaign": self.campaign,
            "date": timezone.now(),
        }

    def test_normal_creation_initializes_one_structured_event_and_serializes(self):
        match = Match.objects.create(**self.match_data())
        event = match.event
        self.assertEqual(event.possession.home.team_id, self.home.pk)
        self.assertEqual(event.possession.away.team_id, self.away.pk)
        self.assertEqual(TeamPossession.objects.count(), 2)
        self.assertEqual(Possession.objects.count(), 1)
        self.assertEqual(Event.objects.count(), 1)
        data = MatchSerializer(match).data
        self.assertEqual(data["id"], match.pk)
        self.assertEqual(data["home_scores_count"], 0)
        self.assertEqual(data["away_scores_count"], 0)

    def test_repeated_initialization_preserves_existing_event_and_possession(self):
        match = Match.objects.create(**self.match_data())
        event = match.event
        home = event.possession.home
        home.possession = 64
        home.save(update_fields=["possession"])
        create_match_event(Match, match, created=True, using="default")
        self.assertEqual(initialize_match_event(match).pk, event.pk)
        home.refresh_from_db()
        self.assertEqual(home.possession, 64)
        self.assertEqual(TeamPossession.objects.count(), 2)
        self.assertEqual(Event.objects.count(), 1)

    def test_raw_fixture_match_does_not_create_unrequested_related_records(self):
        match = Match(**self.match_data())
        match.save_base(raw=True)
        self.assertFalse(Event.objects.exists())
        self.assertFalse(Possession.objects.exists())
        self.assertFalse(TeamPossession.objects.exists())
        match.day = 2
        match.save(update_fields=["day"])
        self.assertFalse(Event.objects.exists())

    def test_api_creation_rolls_back_match_and_all_initializer_rows_on_failure(self):
        original_create = QuerySet.create

        def fail_event_creation(queryset, **kwargs):
            if queryset.model is Event:
                raise RuntimeError("Simulated event write failure")
            return original_create(queryset, **kwargs)

        with (
            patch.object(QuerySet, "create", new=fail_event_creation),
            self.assertRaisesMessage(RuntimeError, "Simulated event write failure"),
        ):
            MatchSerializer().create(self.match_data())
        for model in (Match, Event, Possession, TeamPossession):
            self.assertEqual(model.objects.count(), 0)

    def test_content_keeps_canonical_sports_relationships_and_identifiers(self):
        match = Match.objects.create(**self.match_data())
        player = Player.objects.create(first_name="Test", last_name="Player", code=1234)
        podcast = Podcast.objects.create(title="Football show")
        episode = Episode.objects.create(podcast=podcast, title="Match analysis")
        relations = {
            "regions": self.region,
            "countries": self.country,
            "competitions": self.league,
            "teams": self.home,
            "players": player,
            "matches": match,
        }
        for content in (podcast, episode):
            identity = (content.pk, str(content.slug))
            for field, entity in relations.items():
                getattr(content, field).add(entity)
            content.refresh_from_db()
            self.assertEqual((content.pk, str(content.slug)), identity)
            for field, entity in relations.items():
                self.assertEqual(list(getattr(content, field).all()), [entity])
