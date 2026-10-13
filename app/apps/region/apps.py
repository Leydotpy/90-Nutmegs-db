from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RegionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.region"
    label = "region"
    verbose_name = _("Region")

    def ready(self):
        from apps.region import receivers  # noqa: F401
