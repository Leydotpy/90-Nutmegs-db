from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ThumbnailConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.thumbnail"
    label = "thumbnail"
    verbose_name = _("Thumbnail")
