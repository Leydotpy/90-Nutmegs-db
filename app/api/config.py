# pylint: disable=W0201

from django.apps import apps
from django.urls import path

from core.application import AppConfig


class Api(AppConfig):
    name = "api"
    label = "api"

    namespace = "api"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rest_apis = None

    def ready(self):

        self._rest_apis = apps.get_app_config("rest")


    def get_urls(self):
        urls = [
            path("rest/", self._rest_apis.urls),
        ]
        return self.post_process_urls(urls)

#  http://localhost:8000/api/rest/web/apps/profile/queue/
