from django.db import transaction
from rest_framework import serializers

from api.rest.web.serializers.media import ImageModelSerializer
from api.rest.web.apps.podcasts.serializers import EpisodeDetailSerializer, PostReactionSerializer
from apps.media.images.models import Image
from apps.media.models import PlayList


class PlayListModelSerializer(serializers.ModelSerializer):
    image = ImageModelSerializer(source="get_image", read_only=True)
    items = EpisodeDetailSerializer(source="get_discoverable_episodes", many=True)
    type = serializers.CharField(source="get_type")
    is_liked = serializers.SerializerMethodField("get_is_liked")
    reactions = PostReactionSerializer(source="get_reactions", many=True)
    my_reaction = serializers.SerializerMethodField("get_my_reaction")
    duration = serializers.CharField(read_only=True)
    raw_duration = serializers.IntegerField(read_only=True, source="get_raw_duration")

    class Meta:
        model = PlayList
        fields = (
            "id",
            "timestamp",
            "description",
            "duration",
            "raw_duration",
            "type",
            "image",
            "items",
            "name",
            "is_liked",
            "reactions",
            "my_reaction",
        )
        read_only_fields = ("items",)

    def get_is_liked(self, obj):
        request = self.context["request"]
        if not request.user.is_authenticated:
            return False
        return obj.check_is_liked(request.user)

    def get_my_reaction(self, obj):
        request = self.context["request"]
        if not request.user.is_authenticated:
            return None
        return PostReactionSerializer(
            obj.get_my_reaction(request.user), context={"request": request}
        ).data

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.save()
        return instance


class PlaylistUserCreateSerializer(serializers.ModelSerializer):
    # allow clients to upload a single image file directly when creating/updating
    file = serializers.ImageField(write_only=True, required=False, allow_null=True)
    image = ImageModelSerializer(read_only=True)

    class Meta:
        model = PlayList
        fields = ("id", "name", "description", "image", "file")

    @staticmethod
    def _attach_uploaded_file(playlist, file_obj, title=None):
        """Create MediaImage, Image (or reuse) and attach to playlist in atomic block."""
        # If you want a deterministic naming convention, build it here
        title = title or f"user_playlist_{playlist.pk or 'new'}"
        with transaction.atomic():
            return Image.objects.create_for_model(
                type(playlist), playlist.pk, file=file_obj, title=title
            )

    def create(self, validated_data):
        file_obj = validated_data.pop("file", None)
        with transaction.atomic():
            playlist = super().create(validated_data)
            if file_obj:
                self._attach_uploaded_file(playlist, file_obj, title=playlist.name)
        return playlist

    def update(self, instance, validated_data):
        file_obj = validated_data.pop("file", None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if file_obj:
                self._attach_uploaded_file(instance, file_obj, title=instance.name)
        return instance
