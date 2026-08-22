from django.urls import path
from django.utils.translation import gettext_lazy as _

from core.application import AppConfig


class MediaStreamingWebAPIConfig(AppConfig):
    label = "media_streaming_web_api"
    name = "api.rest.web.apps.media.streaming"
    verbose_name = _("Media Streaming Web Api")
    verbose_name_plural = _("Media Streaming Web Api")

    namespace = "media_streaming_web_api"

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.episode_streaming_view = None


    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        from api.rest.web.apps.media.streaming.views import (
            stream_episode_progressive
        )

        self.episode_streaming_view = stream_episode_progressive


    def get_urls(self):
        urls = [
            path("episodes/<uuid:episode_id>/stream/", self.episode_streaming_view, name="stream_episode_progressive"),
        ]
        return self.post_process_urls(urls)
