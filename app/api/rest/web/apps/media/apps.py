from django.apps import apps
from django.urls import path
from django.utils.translation import gettext_lazy as _

from core.application import AppConfig


class MediaWebAPIConfig(AppConfig):
    label = "media_web_api"
    name = "api.rest.web.apps.media"
    verbose_name = _("Media Web Api")

    namespace = "media_web_api"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.media_offline_api = None
        self.streaming_api = None
        self._media_audio_api = None


    # pylint: disable=attribute-defined-outside-init
    def ready(self):

        self.streaming_api = apps.get_app_config("media_streaming_web_api")
        self.media_offline_api = apps.get_app_config("media_offline_web_api")
        self._media_audio_api = apps.get_app_config("media_audio_api")


    def get_urls(self):
        urls = [
            path("audio/", self._media_audio_api.urls, name="media-offline"),
            path("offline/", self.media_offline_api.urls, name="media-offline"),
            path("streaming/", self.streaming_api.urls, name="media-streaming"),
        ]
        return self.post_process_urls(urls)
