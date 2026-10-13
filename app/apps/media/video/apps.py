from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VideoAppConfig(AppConfig):
    name = "apps.media.video"
    label = "video"
    verbose_name = _("Video")
    verbose_name_plural = _("Videos")
