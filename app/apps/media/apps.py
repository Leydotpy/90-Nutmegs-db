from django.utils.translation import gettext_lazy as _
from core.application import AppConfig


class MediaConfig(AppConfig):
    name = "apps.media"
    label = "media"
    verbose_name = _("Media")

    namespace = "media"

    def ready(self):
        from . import receivers # noqa
