from django.db.models.signals import pre_save
from django.dispatch import receiver
from utils.utils import generate_code

from apps.region.models import Country, Region


@receiver(pre_save, sender=Region)
def generate_code_for_region(sender, instance, raw=False, using=None, **kwargs):
    if not raw and instance.code is None:
        instance.code = int(generate_code(4, klass=sender, using=using))


@receiver(pre_save, sender=Country)
def generate_code_for_country(sender, instance, raw=False, using=None, **kwargs):
    if not raw and instance.code is None:
        instance.code = int(generate_code(4, klass=sender, using=using))
