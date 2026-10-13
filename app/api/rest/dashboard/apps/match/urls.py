from django.urls import include, path

from api.rest.dashboard.apps.match.views import MatchViewSet
from api.rest.dashboard.routers import StaffRouter

router = StaffRouter()
router.register(r"", MatchViewSet, basename="match")

urlpatterns = [path("", include(router.urls))]
