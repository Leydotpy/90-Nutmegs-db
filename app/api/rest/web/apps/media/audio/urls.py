from django.urls import path

from api.rest.web.apps.media.audio.views import MediaAudioAPIView

urlpatterns = [path("add/", MediaAudioAPIView.as_view(), name="add_audio")]
