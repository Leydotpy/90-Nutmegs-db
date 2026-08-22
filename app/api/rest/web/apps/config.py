# pylint: disable=W0201

from django.apps import apps
from django.urls import path

from core.application import AppConfig


class ApiAppConfig(AppConfig):
    name = "api.rest.web.apps"
    label = "api_apps"

    namespace = "api_apps"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._media_api = None
        self._podcast_api = None
        self._profile_api = None
        self._comment_api = None
        self._queue_api = None

    def ready(self):
        self._media_api = apps.get_app_config("media_web_api")
        self._podcast_api = apps.get_app_config("podcast_web_api")
        self._profile_api = apps.get_app_config("profile_web_api")
        self._comment_api = apps.get_app_config("comment_web_api")
        self._queue_api = apps.get_app_config("queue_web_api")

    def get_urls(self):
        urls = [
            path("media/", self._media_api.urls),
            path("podcast/", self._podcast_api.urls),
            path("profile/", self._profile_api.urls),
            path("comment/", self._comment_api.urls),
            path("queue/", self._queue_api.urls),
        ]
        return self.post_process_urls(urls)


# http://localhost:8000/api/rest/web/apps/media/streaming/...