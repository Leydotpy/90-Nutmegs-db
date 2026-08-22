from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .access import AccessService
from .models import Entitlement, Subscription
from ..recommendation.cache import invalidate_user_recommendations

service = AccessService.get_instance()


@receiver(post_save, sender=Entitlement)
@receiver(post_delete, sender=Entitlement)
def on_entitlement_changed(sender, instance, **kwargs):
    try:
        service.invalidate_user_cache(instance.user)
    except Exception:
        pass


@receiver(post_save, sender=Subscription)
@receiver(post_delete, sender=Subscription)
def on_subscription_changed(sender, instance, **kwargs):
    try:
        user = instance.membership.user
        service.invalidate_user_cache(user)
        invalidate_user_recommendations(user.id)
    except Exception:
        pass
