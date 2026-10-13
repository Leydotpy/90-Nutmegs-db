from django.urls import include, path

app_name = "api_apps"

urlpatterns = [
    path("media/", include("api.rest.web.apps.media.urls")),
    path("podcast/", include("api.rest.web.apps.podcasts.urls")),
    path("profile/", include("api.rest.web.apps.profile.urls")),
    path("comment/", include("api.rest.web.apps.comments.urls")),
    path("queue/", include("api.rest.web.apps.queue.urls")),
]
