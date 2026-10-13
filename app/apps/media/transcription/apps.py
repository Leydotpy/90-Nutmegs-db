from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TranscriptionConfig(AppConfig):
    name = "apps.media.transcription"
    label = "transcription"

    verbose_name = _("Transcription")
    verbose_name_plural = _("Transcription")

    def ready(self):
        from . import receivers  # noqa: F401
