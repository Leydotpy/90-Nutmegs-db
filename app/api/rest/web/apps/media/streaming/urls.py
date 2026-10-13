from django.urls import path

from api.rest.web.apps.media.streaming.views import stream_episode_progressive

app_name = "media_streaming_web_api"

urlpatterns = [
    path(
        "episodes/<uuid:episode_id>/stream/",
        stream_episode_progressive,
        name="stream_episode_progressive",
    ),
]
