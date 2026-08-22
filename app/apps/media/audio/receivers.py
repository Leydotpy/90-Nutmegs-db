from django.db.models.signals import post_save
from django.dispatch import receiver

from helpers.tasks import delay_on_commit
from .models import Audio
from .tasks import process_audio


@receiver(post_save, sender=Audio)
def audio_post_save(sender, instance, created, **kwargs):
    if created and instance.master and not instance.processed:
        # process_audio.delay(str(instance.id))
        delay_on_commit(process_audio, str(instance.id))
        # process_audio.delay(str(instance.id))
