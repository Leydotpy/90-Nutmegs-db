from core.application import AppConfig
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from rest_framework import routers


class PodcastDashboardConfig(AppConfig):
    name = 'api.rest.dashboard.apps.podcasts'
    label = 'podcasts_dashboard_api'
    verbose_name = _('Podcasts Dashboard API')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._router = None

    def ready(self):
        from api.rest.dashboard.apps.podcasts.views import (
            EpisodeViewSet,
            PodcastViewSet,
            SeasonViewSet,
        )
        self._router = routers.DefaultRouter()
        self._router.register(r"seasons", SeasonViewSet, basename="season")
        self._router.register(r"episodes", EpisodeViewSet, basename="episode")
        self._router.register(r"", PodcastViewSet, basename="podcasts")

    def get_urls(self):
        urls = [
            path("", include(self._router.urls)),
        ]
        return self.post_process_urls(urls)
