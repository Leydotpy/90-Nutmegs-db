from django.utils.translation import gettext_lazy as _
from core.application import AppConfig


class PromotionsConfig(AppConfig):
    name = 'apps.promotions'
    label = "promotions"
    verbose_name = _("Promotions")

    namespace = "promotions"

    def ready(self):
        from . import receivers
