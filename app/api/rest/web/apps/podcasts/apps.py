from django.urls import path
from django.utils.translation import gettext_lazy as _

from core.application import AppConfig


class PodcastWebAPIConfig(AppConfig):
    label = "podcast_web_api"
    name = "api.rest.web.apps.podcasts"
    verbose_name = _("Podcast Web Api")

    namespace = "podcast_web_api"

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self._auto = None
    #     self._handpicked = None
    #     self._episode_detail = None
    #     self._podcast_detail = None
    #     self._trending_podcasts = None
    #     self._promotions_view = None
    #     self._episode_list = None
    #     self._recently_view = None
    #     self._recently_played = None
    #     self._update_playback = None
    #     self._uncompleted_playbacks = None


    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        from api.rest.web.apps.podcasts.views import (
            AutomaticPromotionAPIView,
            HandpickedPromotionsAPIView,
            EpisodeDetailAPIView,
            PodcastDetailAPIView,
            PromotionsAPIView,
            EpisodeListAPIView,
            TrendingPodcastAPIView,
            RecentlyViewedPodcastAPIView,
            PlayBackListApiView,
            PlaybackUpdateAPIView,
            PlaybackUncompletedListAPIView,
        )
        self._auto = AutomaticPromotionAPIView
        self._handpicked = HandpickedPromotionsAPIView
        self._episode_detail = EpisodeDetailAPIView
        self._podcast_detail = PodcastDetailAPIView
        self._trending_podcasts = TrendingPodcastAPIView
        self._promotions_view = PromotionsAPIView
        self._episode_list = EpisodeListAPIView
        self._recently_view = RecentlyViewedPodcastAPIView
        self._recently_played = PlayBackListApiView
        self._update_playback = PlaybackUpdateAPIView
        self._uncompleted_playbacks = PlaybackUncompletedListAPIView


    def get_urls(self):
        urls = [
            path("auto/", self._auto.as_view(), name="auto"),
            path("handpicked/", self._handpicked.as_view(), name="handpicked"),
            path("promotions/", self._promotions_view.as_view(), name="promotions"),
            path("trending/", self._trending_podcasts.as_view(), name="trending-podcast"),
            path("recently-viewed/", self._recently_view.as_view(), name="recently-viewed"),
            path("recently-played/", self._recently_played.as_view(), name="recently-played"),
            path("resume-playback/", self._uncompleted_playbacks.as_view(), name="resume-playback"),
            path("<slug:slug>/", self._podcast_detail.as_view(), name="podcast-detail"),
            path("<slug:slug>/episodes/", self._episode_list.as_view(), name="episodes-list"),
            path("episode/<slug:slug>/", self._episode_detail.as_view(), name="episode-detail"),
            path("episode/<slug:slug>/update-playback", self._update_playback.as_view(), name="episode-update-playback"),
        ]
        return self.post_process_urls(urls)
