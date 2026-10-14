from django.db.models.signals import pre_save
from django.dispatch import receiver
from utils.utils import generate_code

from apps.region.leagues.clubs.models import Team


@receiver(pre_save, sender=Team)
def team_code_generate_fn(sender, instance, raw=False, using=None, **kwargs):
    if not raw and instance.code is None:
        instance.code = int(generate_code(4, klass=sender, using=using))
