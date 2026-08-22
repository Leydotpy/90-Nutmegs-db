from rest_framework import serializers

from api.rest.web.apps.podcasts.serializers import EpisodeDetailSerializer, AppLabel
from api.rest.web.serializers.auth import UserDisplaySerializer
from apps.queue.models import Queue, QueueItem


class QueueItemSerializer(serializers.ModelSerializer):
    track = EpisodeDetailSerializer(read_only=True)
    count = serializers.IntegerField(read_only=True)

    class Meta:
        model = QueueItem
        fields = ("id", "queue_id", "track", "count", "position", "timestamp", "order", "added_at")


class QueueModelSerializer(serializers.ModelSerializer):
    app_label = serializers.ChoiceField(write_only=True, choices=AppLabel.choices, default=AppLabel.PODCAST)
    item_id = serializers.CharField(write_only=True)
    tracks = QueueItemSerializer(many=True, read_only=True)
    owner = UserDisplaySerializer(read_only=True)

    class Meta:
        model = Queue
        fields = (
            "id",
            "tracks", "created_at", "date_merged", "frozen",
            "updated", "app_label", "item_id", "last_activity", "owner"
        )

        read_only_fields = ("frozen", "date_merged")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = None

    def update(self, instance: Queue, validated_data):
        return instance.add_item(**validated_data)


class QueueItemModelSerializer(serializers.ModelSerializer):
    track = EpisodeDetailSerializer(read_only=True)
    count = serializers.IntegerField(read_only=True)

    class Meta:
        model = QueueItem
        fields = ("id", "count", "queue_id", "track", "position", "timestamp")


class QueueAddItemSerializer(serializers.Serializer):
    item_id = serializers.CharField()
    app_label = serializers.ChoiceField(choices=AppLabel.choices, default=AppLabel.PODCAST)
    override = serializers.BooleanField(default=False, help_text="If True, adds item to the top of the queue.")

    def validate(self, attrs):
        # Optional: Add validation logic here to ensure item_id exists
        # inside the specific AppLabel model if you want strict validation before the view.
        return attrs
