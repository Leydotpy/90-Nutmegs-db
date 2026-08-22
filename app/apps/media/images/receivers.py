from django.db.models.signals import post_save
from django.dispatch import receiver


from .models import Image
from ..utils import generate_image_thumbnail


@receiver(post_save, sender=Image)
def image_post_save_receiver(sender, instance, created, **kwargs):
    if created:
        generate_image_thumbnail(instance)