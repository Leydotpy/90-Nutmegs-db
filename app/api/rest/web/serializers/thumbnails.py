from rest_framework import serializers

from apps.thumbnail.models import Thumbnail


class ThumbnailModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Thumbnail
        fields = ("id", "type", "media", "width", "height", "timestamp")


