from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TacticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tactics"
    label = "tactics"
    verbose_name = _("Tactics")
    verbose_name_plural = _("Tactics")

    def ready(self):
        from . import receiver  # noqa: F401
