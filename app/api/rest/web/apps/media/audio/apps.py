from django.urls import path
from django.utils.translation import gettext_lazy as _

from core.application import AppConfig


class MediaAudioAppConfig(AppConfig):
    name = 'api.rest.web.apps.media.audio'
    label = 'media_audio_api'
    verbose_name = _('Media Audio')
    verbose_name_plural = _('Media Audios')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_audio_view = None

    def ready(self):
        from api.rest.web.apps.media.audio.views import MediaAudioAPIView
        self._add_audio_view = MediaAudioAPIView

    def get_urls(self):
        urls = [
            path("add/", self._add_audio_view.as_view(), name="add_audio"),
        ]
        return self.post_process_urls(urls)
