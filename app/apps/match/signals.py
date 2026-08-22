from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Match, Event, Possession, TeamPossession

@receiver(post_save, sender=Match)
def create_match_event(sender, instance, created, **kwargs):
    if created:
        home_pos = TeamPossession.objects.create(team=instance.home_team)
        away_pos = TeamPossession.objects.create(team=instance.away_team)

        possession = Possession.objects.create(
            home=home_pos,
            away=away_pos
        )

        Event.objects.create(match=instance, possession=possession)

