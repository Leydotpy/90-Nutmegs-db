"""Dashboard serializers for generic image attachments."""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from api.rest.web.serializers.thumbnails import ThumbnailModelSerializer
from apps.media.images.models import Image
from utils.generic_relations import normalize_generic_object_id


class ImageSerializer(serializers.ModelSerializer):
    """Serializer used for both nested image reads and dashboard uploads."""

    file = serializers.ImageField(required=False, allow_null=True)
    id = serializers.UUIDField(read_only=True)
    url = serializers.SerializerMethodField()
    thumbnails = ThumbnailModelSerializer(read_only=True, many=True, source="get_thumbnails")

    class Meta:
        model = Image
        fields = [
            "id",
            "title",
            "file",
            "url",
            "filename",
            "size",
            "width",
            "height",
            "timestamp",
            "thumbnails",
        ]
        read_only_fields = ["id", "url", "filename", "size", "width", "height", "timestamp", "thumbnails"]

    def get_url(self, obj):
        return obj.url


def _create_image_for_instance(instance, image_data):
    """Create a generic image attachment for the supplied model instance."""
    content_type = ContentType.objects.get_for_model(instance.__class__)
    return Image.objects.create(
        content_type=content_type,
        object_id=normalize_generic_object_id(instance.pk),
        **image_data,
    )
