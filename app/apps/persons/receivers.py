from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.persons.models import Player, Fitness
from utils.utils import generate_code


@receiver(post_save, sender=Player)
def player_post_save(sender, instance, created, **kwargs):
    if created:
        Fitness.objects.create(player=instance)

    if not instance.code:
        instance.code = int(generate_code(4, klass=instance.__class__))
        instance.save()