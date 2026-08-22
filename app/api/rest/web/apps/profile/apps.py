from django.urls import path
from django.utils.translation import gettext_lazy as _

from core.application import AppConfig


class ProfileWebAPIConfig(AppConfig):
    label = "profile_web_api"
    name = "api.rest.web.apps.profile"
    verbose_name = _("Profile Web Api")

    namespace = "profile_web_api"

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        from api.rest.web.apps.profile.views import (
            UserSubscriptionAPIView,
            FeaturedPlayListAPIView,
            # ReactToModelAPIView,
            SubscribedListPodcastAPIView,
            PlaylistUserViewSet
        )

        self.featured_playlist = FeaturedPlayListAPIView
        # self.react_to_model = ReactToModelAPIView
        self.user_subscription = UserSubscriptionAPIView
        self.subscribed_list = SubscribedListPodcastAPIView
        self.add_to_playlist = PlaylistUserViewSet.as_view({"post": "add_item"})
        self.remove_from_playlist = PlaylistUserViewSet.as_view({"post": "remove_item"})
        self.reorder_playlist = PlaylistUserViewSet.as_view({"post": "reorder"})
        self.playlist_view = PlaylistUserViewSet.as_view(
            {
                "get": "view_item",
                "put": "update",
                "delete": "destroy",
                "patch": "partial_update"
            }
        )
        self.playlist_list_create_view = PlaylistUserViewSet.as_view(
            {
                "get": "list",
                "post": "create"
            }
        )

    def get_urls(self):
        urls = [
            #path("react/", self.react_to_model.as_view(), name="react-to-model"),
            path("subscribe/", self.user_subscription.as_view(), name="user-subscription"),
            #path("react/<int:id>/", self.react_to_model.as_view(), name="update-reaction"),
            path("subscriptions/podcast/", self.subscribed_list.as_view(), name="subscriptions"),
            path("playlists/featured/", self.featured_playlist.as_view(), name="featured-playlist"),
            path("playlists/", self.playlist_list_create_view, name="add-to-playlist"),
            path("playlists/<int:pk>/", self.playlist_view, name="playlist-detail"),
            path("playlist/<int:pk>/add", self.add_to_playlist, name="add-to-playlist"),
            path("playlist/<int:pk>/remove", self.remove_from_playlist, name="remove-from-playlist"),
            path("playlist/<int:pk>/reorder", self.reorder_playlist, name="reorder-playlist"),

        ]
        return self.post_process_urls(urls)
