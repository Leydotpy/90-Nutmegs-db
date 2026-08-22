from django.utils.translation import gettext_lazy as _
from core.application import AppConfig


class ImagesConfig(AppConfig):
    name = "apps.media.images"
    label = "images"
    verbose_name = _("Images")

    namespace = "images"

    def ready(self):
        from . import receivers # noqa
