from django.urls import path, include
from django.utils.translation import gettext_lazy as _

from django.apps import apps
from core.application import AppConfig


class DashboardAppsConfig(AppConfig):
    name = 'api.rest.dashboard.apps'
    label = 'dashboard_apps_api'
    verbose_name = _('Dashboard apps API')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._podcast_dashboard_api = None
        self._promotions_dashboard_api = None
        self._match_dashboard_api = None
        self._persons_dashboard_api = None
        self._region_dashboard_api = None
        self._membership_dashboard_api = None

    def ready(self):
        self._podcast_dashboard_api = apps.get_app_config('podcasts_dashboard_api')
        self._promotions_dashboard_api = apps.get_app_config('promotions_dashboard_api')
        self._match_dashboard_api = apps.get_app_config('match_dashboard_api')
        self._persons_dashboard_api = apps.get_app_config('persons_dashboard_api')
        self._region_dashboard_api = apps.get_app_config('region_dashboard_api')
        self._membership_dashboard_api = apps.get_app_config('membership_dashboard_api')


    def get_urls(self):
        urls = [
            path("matches/", self._match_dashboard_api.urls),
            path("memberships/", self._membership_dashboard_api.urls),
            path("podcasts/", self._podcast_dashboard_api.urls),
            path("promotions/", self._promotions_dashboard_api.urls),
            path("persons/", self._persons_dashboard_api.urls),
            path("regions/", self._region_dashboard_api.urls),
        ]
        return self.post_process_urls(urls)
