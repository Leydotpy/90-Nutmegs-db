from django.utils.translation import gettext_lazy as _
from django.urls import path, include

from rest_framework import routers
from core.application import AppConfig


class RegionDashboardAPIConfig(AppConfig):
    name = 'api.rest.dashboard.apps.region'
    label = 'region_dashboard_api'
    verbose_name = _('Region Dashboard API')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._router = None
        self._countries = None
        self._leagues = None
        self._teams = None

    def ready(self):
        from api.rest.dashboard.apps.region.views import RegionViewSet, CountryListAPIView, LeagueListAPIView, TeamListAPIView
        self._router = routers.DefaultRouter()
        self._router.register(r"", RegionViewSet, basename="region")
        self._countries = CountryListAPIView.as_view()
        self._leagues = LeagueListAPIView.as_view()
        self._teams = TeamListAPIView.as_view()

    def get_urls(self):
        urls = [
            path('countries/', self._countries),
            path('leagues/', self._leagues),
            path('teams/', self._teams),
            path('', include(self._router.urls)),
        ]
        return self.post_process_urls(urls)