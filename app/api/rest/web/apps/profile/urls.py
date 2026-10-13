from django.urls import path

from api.rest.web.apps.profile.views import (
    FeaturedPlayListAPIView,
    PlaylistUserViewSet,
    SubscribedListPodcastAPIView,
    UserSubscriptionAPIView,
)

app_name = "profile_web_api"

urlpatterns = [
    path("subscribe/", UserSubscriptionAPIView.as_view(), name="user-subscription"),
    path("subscriptions/podcast/", SubscribedListPodcastAPIView.as_view(), name="subscriptions"),
    path("playlists/featured/", FeaturedPlayListAPIView.as_view(), name="featured-playlist"),
    path(
        "playlists/",
        PlaylistUserViewSet.as_view({"get": "list", "post": "create"}),
        name="add-to-playlist",
    ),
    path(
        "playlists/<int:pk>/",
        PlaylistUserViewSet.as_view(
            {
                "get": "view_item",
                "put": "update",
                "delete": "destroy",
                "patch": "partial_update",
            }
        ),
        name="playlist-detail",
    ),
    path(
        "playlist/<int:pk>/add",
        PlaylistUserViewSet.as_view({"post": "add_item"}),
        name="add-to-playlist",
    ),
    path(
        "playlist/<int:pk>/remove",
        PlaylistUserViewSet.as_view({"post": "remove_item"}),
        name="remove-from-playlist",
    ),
    path(
        "playlist/<int:pk>/reorder",
        PlaylistUserViewSet.as_view({"post": "reorder"}),
        name="reorder-playlist",
    ),
]
