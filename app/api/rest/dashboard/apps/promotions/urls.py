from django.urls import include, path

from api.rest.dashboard.apps.promotions.views import (
    GiffyCallbackAPIView,
    ImagePromotionViewSet,
)
from api.rest.dashboard.routers import StaffRouter

app_name = "promotions_dashboard_api"

router = StaffRouter()
router.register(r"images", ImagePromotionViewSet, basename="promotion-image")

urlpatterns = [
    path("", include(router.urls)),
    path("callbacks/giffy/", GiffyCallbackAPIView.as_view(), name="giffy-callback"),
]
