from django.urls import path, include
from django.utils.translation import gettext_lazy as _
from rest_framework.routers import DefaultRouter

from core.application import OscarDashboardConfig


class MembershipDashboardConfig(OscarDashboardConfig):
    name = 'api.rest.dashboard.apps.memberships'
    label = 'membership_dashboard_api'

    verbose_name = _('Membership Dashboard')
    verbose_name_plural = _('Membership Dashboard')

    namespace = 'memberships'

    permissions_map = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._router = None

    def ready(self):
        from api.rest.dashboard.apps.memberships.views import (
            FeatureViewSet,
            PlanViewSet,
            PlanFeatureViewSet,
            EntitlementViewSet,
            MembershipViewSet,
            SubscriptionViewSet,
        )

        self._router = DefaultRouter()
        self._router.register(r'features', FeatureViewSet, basename='feature')
        self._router.register(r'plans', PlanViewSet, basename='plan')
        self._router.register(r'plan-features', PlanFeatureViewSet, basename='planfeature')
        self._router.register(r'entitlements', EntitlementViewSet, basename='entitlement')
        self._router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
        self._router.register(r'', MembershipViewSet, basename='membership')

    def get_urls(self):
        urlpatterns = [
            path('', include(self._router.urls)),
        ]
        return self.post_process_urls(urlpatterns)
