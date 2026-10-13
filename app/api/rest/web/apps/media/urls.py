from django.urls import include, path

app_name = "media_web_api"

urlpatterns = [
    path("audio/", ("api.rest.web.apps.media.audio.urls", "media_audio_api", None)),
    path("offline/", include("api.rest.web.apps.media.offline.urls")),
    path("streaming/", include("api.rest.web.apps.media.streaming.urls")),
]
