from django.db import router, transaction

from .models import Event, Match, Possession, TeamPossession


def initialize_match_event(match, *, using=None):
    """Initialize the existing match structure without replacing recorded data.

    API and admin creation wrap the match and its initializer in one transaction.
    The row lock serializes repeated initialization; historical matches are not
    backfilled automatically because empty results may be misleading.
    """
    using = using or router.db_for_write(Match, instance=match)
    with transaction.atomic(using=using):
        stored_match = Match.objects.using(using).select_for_update().get(pk=match.pk)
        existing = Event.objects.using(using).filter(match_id=match.pk).first()
        if existing is not None:
            return existing
        home = TeamPossession.objects.using(using).create(team_id=stored_match.home_team_id)
        away = TeamPossession.objects.using(using).create(team_id=stored_match.away_team_id)
        possession = Possession.objects.using(using).create(home=home, away=away)
        return Event.objects.using(using).create(match=stored_match, possession=possession)
