from django.dispatch import receiver
from django.db.models.signals import post_save
from apps.media.models import MediaSettings
from core.compat import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def profile_post_save(sender, instance: User, created, **kwargs):
    if created:
        MediaSettings.objects.get_or_create(user=instance)