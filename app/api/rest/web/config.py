# pylint: disable=W0201

from django.apps import apps
from django.urls import path

from core.application import AppConfig


class RestApiWebConfig(AppConfig):
    label = "rest_web"
    name = "api.rest.web"

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self._explore_view = None
    #     self._web_apis = None

    def ready(self):
        from api.rest.web.views import ExploreAPIView

        self._explore_view = ExploreAPIView
        self._web_apis = apps.get_app_config("api_apps")

    def get_urls(self):
        urls = [
            path("apps/", self._web_apis.urls),
            path("explore/", self._explore_view.as_view(), name="explore"),
        ]
        return self.post_process_urls(urls)
