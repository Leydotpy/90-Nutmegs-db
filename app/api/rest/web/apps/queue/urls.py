from django.urls import path

from api.rest.web.apps.queue.views import QueueViewSet

app_name = "queue_web_api"

urlpatterns = [
    path("", QueueViewSet.as_view({"get": "list"}), name="queue"),
    path("add/", QueueViewSet.as_view({"post": "add"}), name="queue-add"),
    path("clear/", QueueViewSet.as_view({"put": "clear"}), name="queue-clear"),
    path(
        "<uuid:episode_id>/remove/",
        QueueViewSet.as_view({"delete": "remove"}),
        name="queue-item-remove",
    ),
]
