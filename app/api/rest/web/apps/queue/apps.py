from django.urls import path
from django.utils.translation import gettext_lazy as _


from core.application import AppConfig


class QueueWebAPIConfig(AppConfig):
    label = "queue_web_api"
    name = "api.rest.web.apps.queue"
    verbose_name = _("Queue Web Api")

    namespace = "queue_web_api"


    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        from api.rest.web.apps.queue.views import (
            QueueViewSet
        )

        # --- ViewSet Action Mappings ---

        # 1. Base Queue (Handles GET list)
        self.queue_list = QueueViewSet.as_view({
            "get": "list",  # Maps GET to the custom 'list' method we discussed
        })

        # 2. Queue Detail (Handles PUT/PATCH/DELETE on a specific Queue instance, though typically used less for single queues)
        self.remove_from_queue = QueueViewSet.as_view({
            "delete": "remove",
        })

        # 3. Custom 'add' action (Handles POST to add items)
        # This maps POST to the custom 'add' method defined in the ViewSet.
        self.queue_add_item = QueueViewSet.as_view({
            "post": "add",
        })

        # 3. Custom 'clear' action (Handles POST to add items)
        # This maps POST to the custom 'clear' method defined in the ViewSet.
        self.queue_clear_items = QueueViewSet.as_view({
            "put": "clear",
        })

        # --- Queue Item Mappings (Example for completeness) ---

        # If you need to manage individual items in the queue, you would define similar mappings for a QueueItemViewSet
        # queue_item_list = QueueItemViewSet.as_view({"get": "list"})



    def get_urls(self):

        urls = [
            path("", self.queue_list, name="queue"),
            path("add/", self.queue_add_item, name="queue-add"),
            path("clear/", self.queue_clear_items, name="queue-clear"),
            path("<int:episode_id>/remove/", self.remove_from_queue, name="queue-item-remove"),

        ]
        return self.post_process_urls(urls)
