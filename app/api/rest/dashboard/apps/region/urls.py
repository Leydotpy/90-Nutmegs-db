from django.urls import include, path

from api.rest.dashboard.apps.region.views import (
    CountryListAPIView,
    LeagueListAPIView,
    RegionViewSet,
    TeamListAPIView,
)
from api.rest.dashboard.routers import StaffRouter

router = StaffRouter()
router.register(r"", RegionViewSet, basename="region")

urlpatterns = [
    path("countries/", CountryListAPIView.as_view()),
    path("leagues/", LeagueListAPIView.as_view()),
    path("teams/", TeamListAPIView.as_view()),
    path("", include(router.urls)),
]
