from django.urls import path, include
from django.utils.translation import gettext_lazy as _
from rest_framework import routers

from core.application import AppConfig


class MatchDashboardAPIConfig(AppConfig):
    name = "api.rest.dashboard.apps.match"
    label = "match_dashboard_api"
    verbose_name = _("Match Dashboard API")


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._router = None


    def ready(self):
        from api.rest.dashboard.apps.match.views import MatchViewSet
        self._router = routers.DefaultRouter()
        self._router.register(r"", MatchViewSet, basename="match")

    def get_urls(self):
        urls = [
            path("", include(self._router.urls)),
        ]
        return self.post_process_urls(urls)