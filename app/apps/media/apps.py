from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MediaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.media"
    label = "media"
    verbose_name = _("Media")

    def ready(self):
        from . import receivers  # noqa: F401
