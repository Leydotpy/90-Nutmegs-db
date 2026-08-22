from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OfflineAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.media.offline"
    label = "offline"
    verbose_name = _("Offline")
    verbose_name_plural = _("Offline")
