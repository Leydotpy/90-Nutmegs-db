from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Match
from .services import initialize_match_event


@receiver(post_save, sender=Match, dispatch_uid="match.initialize_event")
def create_match_event(sender, instance, created, raw=False, using=None, **kwargs):
    if created and not raw:
        initialize_match_event(instance, using=using)
