from django.urls import include, path

from api.rest.dashboard.apps.persons.views import PlayerViewSet, StaffViewSet
from api.rest.dashboard.routers import StaffRouter

router = StaffRouter()
router.register(r"players", PlayerViewSet, basename="player")
router.register(r"staff", StaffViewSet, basename="staff")

urlpatterns = [path("", include(router.urls))]
