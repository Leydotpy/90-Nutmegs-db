from django.db import models
from django.dispatch import receiver

from core.compat import get_user_model

from .models import UserTranscriptionQuota

User = get_user_model()


@receiver(models.signals.post_save, sender=User)
def create_transcription_quota(sender, instance, created, **kwargs):
    if created:
        UserTranscriptionQuota.objects.create(user=instance)