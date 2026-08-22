# pylint: disable=W0201

from django.apps import apps
from django.urls import path

from core.application import AppConfig


class RestApiConfig(AppConfig):
    label = "rest"
    name = "api.rest"

    def __init__(self, *args, **kwargs):
        super(RestApiConfig, self).__init__(*args, **kwargs)
        self._web_apis = None
        self._dashboard_apis = None

    def ready(self):
        self._web_apis = apps.get_app_config("rest_web")
        self._dashboard_apis = apps.get_app_config("dashboard_api")

    def get_urls(self):
        urls = [
            path("web/", self._web_apis.urls),
            path("dashboard/", self._dashboard_apis.urls),
        ]
        return self.post_process_urls(urls)
