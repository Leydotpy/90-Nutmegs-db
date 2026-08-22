# apps/media/api/serializers.py
from rest_framework import serializers

from apps.media.offline.models import Device, License
from apps.posts.podcasts.models import Episode


class DeviceRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["device_id", "name", "device_type", "platform", "public_key_pem", "metadata", "max_offline_items"]

    def create(self, validated_data):
        user = self.context["request"].user
        device, created = Device.objects.update_or_create(
            user=user, device_id=validated_data["device_id"],
            defaults={
                "name": validated_data.get("name", ""),
                "device_type": validated_data.get("device_type", "other"),
                "platform": validated_data.get("platform", ""),
                "public_key_pem": validated_data.get("public_key_pem"),
                "metadata": validated_data.get("metadata", {}),
                "max_offline_items": validated_data.get("max_offline_items"),
            }
        )
        return device


class OfflineRequestSerializer(serializers.Serializer):
    episode_id = serializers.UUIDField()
    preset = serializers.CharField(default="medium")
    device_id = serializers.CharField()
    days_valid = serializers.IntegerField(default=7)
    max_plays = serializers.IntegerField(required=False)

    def validate(self, data):
        # check episode exists & offline allowed
        try:
            episode = Episode.objects.get(pk=data["episode_id"])
        except Episode.DoesNotExist:
            raise serializers.ValidationError("Episode not found")
        if not getattr(episode, "offline_allowed", False):
            raise serializers.ValidationError("Offline downloads are not allowed for this episode")
        data["episode"] = episode
        return data


class OfflineLicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = ["id", "package", "device", "issued_at", "expires_at", "max_plays", "plays", "revoked"]
        read_only_fields = ["id", "issued_at", "plays"]
