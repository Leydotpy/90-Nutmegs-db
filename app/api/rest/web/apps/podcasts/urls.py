from django.urls import path

from api.rest.web.apps.podcasts.views import (
    AutomaticPromotionAPIView,
    EpisodeDetailAPIView,
    EpisodeListAPIView,
    HandpickedPromotionsAPIView,
    PlayBackListApiView,
    PlaybackUncompletedListAPIView,
    PlaybackUpdateAPIView,
    PodcastDetailAPIView,
    PromotionsAPIView,
    RecentlyViewedPodcastAPIView,
    TrendingPodcastAPIView,
)

app_name = "podcast_web_api"

urlpatterns = [
    path("auto/", AutomaticPromotionAPIView.as_view(), name="auto"),
    path("handpicked/", HandpickedPromotionsAPIView.as_view(), name="handpicked"),
    path("promotions/", PromotionsAPIView.as_view(), name="promotions"),
    path("trending/", TrendingPodcastAPIView.as_view(), name="trending-podcast"),
    path("recently-viewed/", RecentlyViewedPodcastAPIView.as_view(), name="recently-viewed"),
    path("recently-played/", PlayBackListApiView.as_view(), name="recently-played"),
    path("resume-playback/", PlaybackUncompletedListAPIView.as_view(), name="resume-playback"),
    path("<slug:slug>/", PodcastDetailAPIView.as_view(), name="podcast-detail"),
    path("<slug:slug>/episodes/", EpisodeListAPIView.as_view(), name="episodes-list"),
    path("episode/<slug:slug>/", EpisodeDetailAPIView.as_view(), name="episode-detail"),
    path(
        "episode/<slug:slug>/update-playback",
        PlaybackUpdateAPIView.as_view(),
        name="episode-update-playback",
    ),
]
