from django.urls import include, path

from api.rest.dashboard.apps.memberships.views import (
    EntitlementViewSet,
    FeatureViewSet,
    MembershipViewSet,
    PlanFeatureViewSet,
    PlanViewSet,
    SubscriptionViewSet,
)
from api.rest.dashboard.routers import StaffRouter

app_name = "membership_dashboard_api"

router = StaffRouter()
router.register(r"features", FeatureViewSet, basename="feature")
router.register(r"plans", PlanViewSet, basename="plan")
router.register(r"plan-features", PlanFeatureViewSet, basename="planfeature")
router.register(r"entitlements", EntitlementViewSet, basename="entitlement")
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")
router.register(r"", MembershipViewSet, basename="membership")

urlpatterns = [path("", include(router.urls))]
