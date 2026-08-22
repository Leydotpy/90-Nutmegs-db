from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.rest.web.apps.queue.serializers import QueueItemSerializer, QueueModelSerializer, QueueAddItemSerializer
from apps.queue.models import Queue
from apps.queue.utils import get_or_create_queue_for_request


class QueueViewSet(viewsets.ModelViewSet):
    queryset = Queue.objects.all()
    serializer_class = QueueModelSerializer

    def list(self, request, *args, **kwargs):
        q = get_or_create_queue_for_request(request)
        q.touch()
        items = q.items.all()
        serializer = QueueItemSerializer(items, many=True, context=self.get_serializer_context())
        return Response({"tracks": serializer.data, "last_activity": q.last_activity})

    @action(detail=False, methods=["post"], url_path="add")
    def add(self, request):
        """
        POST /queues/add/
        Payload: { "item_id": "uuid-or-pk", "app_label": "podcasts.Podcast", "override": true }
        """
        # 1. Get or Create the Queue for the user
        queue = get_or_create_queue_for_request(request)

        # 2. Validate Input
        input_serializer = QueueAddItemSerializer(data=request.data, context=self.get_serializer_context())
        input_serializer.is_valid(raise_exception=True)

        data = input_serializer.validated_data

        try:
            with transaction.atomic():
                # 3. Call the model logic
                queue.add_item(
                    item_id=data['item_id'],
                    app_label=data['app_label'],
                    override=data['override']
                )

                # 4. Touch updated timestamp
                queue.touch()

        except Exception as e:
            # Handle specific exceptions (like ItemNotFound) gracefully here
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 5. Return the updated queue items or just a success message
        # Returning the updated list allows the frontend to update immediately
        items = queue.items.all().order_by('position')
        return Response(
            QueueItemSerializer(items, many=True, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["delete"])
    def remove(self, request):
        q = get_or_create_queue_for_request(request)
        episode_id = self.kwargs.get("episode_id")
        # episode_id = request.data.get("episode_id")
        deleted, _ = q.items.filter(episode_id=episode_id).delete()
        q.touch()
        return Response({"deleted": deleted})

    @action(detail=False, methods=["post"])
    def play(self, request):
        # indicate interaction; update last_activity and maybe track play_count or position
        q = get_or_create_queue_for_request(request)
        q.touch()
        return Response({"status": "ok"})

    @action(detail=False, methods=["put"])
    def clear(self, request):
        q = get_or_create_queue_for_request(request)
        q.items.all().delete()
        # If logged-in user, you can keep queue but empty; if anonymous you may freeze or delete.
        if not (request.user and request.user.is_authenticated):
            # keep anon queue but it will expire via cleanup based on last_activity
            q.touch()
        else:
            # logged-in users: maybe freeze or leave for next time. Per your rule, you want queue to expire when emptied;
            # either delete record or set frozen flag
            q.frozen = True
            q.save(update_fields=["frozen"])
        return Response({"status": "cleared"})
