from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.apps import apps

from core.application import AppConfig


class DashboardConfig(AppConfig):
    name = 'api.rest.dashboard'
    label = 'dashboard_api'
    verbose_name = _('Dashboard API')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dashboard_apps_api = None
        self._spectacular_api_view = None
        self._spectacular_redoc_view = None
        self._spectacular_swagger_view = None

    def ready(self):
        from drf_spectacular.views import (
            SpectacularAPIView,
            SpectacularRedocView,
            SpectacularSwaggerView
        )
        self._dashboard_apps_api = apps.get_app_config('dashboard_apps_api')
        self._spectacular_api_view = SpectacularAPIView
        self._spectacular_swagger_view = SpectacularSwaggerView
        self._spectacular_redoc_view = SpectacularRedocView


    def get_urls(self):
        urls = [
            path("apps/", self._dashboard_apps_api.urls),
            path("schema/", self._spectacular_api_view.as_view(), name="schema"),
            path("schema/swagger-ui/", self._spectacular_swagger_view.as_view(url_name="schema"), name="swagger-ui"),
            path("schema/redoc/", self._spectacular_redoc_view.as_view(url_name="schema"), name="redoc"),
        ]
        return self.post_process_urls(urls)