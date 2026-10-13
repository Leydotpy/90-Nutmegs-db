from django.urls import include, path

from api.rest.dashboard.apps.podcasts.views import (
    EpisodeViewSet,
    PodcastViewSet,
    SeasonViewSet,
)
from api.rest.dashboard.routers import StaffRouter

router = StaffRouter()
router.register(r"seasons", SeasonViewSet, basename="season")
router.register(r"episodes", EpisodeViewSet, basename="episode")
router.register(r"", PodcastViewSet, basename="podcasts")

urlpatterns = [path("", include(router.urls))]
