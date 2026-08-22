"""Dashboard routing for promotions management APIs."""

from __future__ import annotations

from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from rest_framework import routers

from core.application import AppConfig


class PromotionsDashboardConfig(AppConfig):
    """Dashboard app config exposing promotion management and service callbacks."""

    name = "api.rest.dashboard.apps.promotions"
    label = "promotions_dashboard_api"
    verbose_name = _("Promotions Dashboard API")
    namespace = "promotions_dashboard_api"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._router = None
        self._giffy_callback_view = None

    def ready(self):
        from api.rest.dashboard.apps.promotions.views import GiffyCallbackAPIView, ImagePromotionViewSet

        self._router = routers.DefaultRouter()
        self._router.register(r"images", ImagePromotionViewSet, basename="promotion-image")
        self._giffy_callback_view = GiffyCallbackAPIView

    def get_urls(self):
        urls = [
            path("", include(self._router.urls)),
            path("callbacks/giffy/", self._giffy_callback_view.as_view(), name="giffy-callback"),
        ]
        return self.post_process_urls(urls)
