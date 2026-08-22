from django.urls import path, include
from django.utils.translation import gettext as _
from rest_framework import routers

from core.application import AppConfig


class PersonsDashboardAPIConfig(AppConfig):
    name = 'api.rest.dashboard.apps.persons'
    label = 'persons_dashboard_api'
    # verbose_name = _('Persons')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._router = None

    def ready(self):
        from api.rest.dashboard.apps.persons.views import (
            PlayerViewSet, StaffViewSet
        )
        self._router = routers.DefaultRouter()
        self._router.register(r"players", PlayerViewSet, basename="player")
        self._router.register(r"staff", StaffViewSet, basename="staff")

    def get_urls(self):
        urls = [
            path("", include(self._router.urls)),
        ]
        return self.post_process_urls(urls)
