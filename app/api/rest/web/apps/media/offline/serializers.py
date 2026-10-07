# apps/media/api/serializers.py
from apps.media.offline.models import Device, License
from apps.media.offline.webhook import validate_callback_url
from apps.posts.podcasts.models import Episode
from rest_framework import serializers


class DeviceRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            "device_id",
            "name",
            "device_type",
            "platform",
            "public_key_pem",
            "metadata",
            "max_offline_items",
        ]
        read_only_fields = ("max_offline_items",)

    def create(self, validated_data):
        user = self.context["request"].user
        device, created = Device.objects.update_or_create(
            user=user,
            device_id=validated_data["device_id"],
            defaults={
                "name": validated_data.get("name", ""),
                "device_type": validated_data.get("device_type", "other"),
                "platform": validated_data.get("platform", ""),
                "public_key_pem": validated_data.get("public_key_pem"),
                "metadata": validated_data.get("metadata", {}),
            },
        )
        return device


class OfflineRequestSerializer(serializers.Serializer):
    episode_id = serializers.UUIDField()
    preset = serializers.ChoiceField(
        choices=("preview", "low", "medium", "high"),
        default="medium",
    )
    device_id = serializers.CharField()
    days_valid = serializers.IntegerField(default=7, min_value=1, max_value=30)
    max_plays = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=10_000,
    )
    callback_url = serializers.URLField(required=False)

    def validate_callback_url(self, value):
        return validate_callback_url(value)

    def validate(self, data):
        # Access is intentionally evaluated by the canonical AccessPolicy in the
        # view.  A serializer must not maintain a second entitlement decision tree.
        try:
            episode = Episode.objects.get(pk=data["episode_id"])
        except Episode.DoesNotExist:
            raise serializers.ValidationError("Episode not found") from None
        data["episode"] = episode
        return data


class OfflineLicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = [
            "id",
            "package",
            "device",
            "issued_at",
            "expires_at",
            "max_plays",
            "plays",
            "revoked",
        ]
        read_only_fields = ["id", "issued_at", "plays"]


class OfflineDetailResponseSerializer(serializers.Serializer):
    """Stable detail envelope used by the transitional offline API."""

    detail = serializers.CharField()


class DeviceRegistrationResponseSerializer(serializers.Serializer):
    device_id = serializers.CharField()
    id = serializers.UUIDField()


class OfflinePackageLicenseResponseSerializer(serializers.Serializer):
    license_id = serializers.UUIDField()
    download_url = serializers.CharField()
    encrypted_dek_for_device = serializers.CharField()
    expires_at = serializers.DateTimeField()


class OfflinePackageAcceptedResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    task_id = serializers.CharField()
    status_url = serializers.CharField()


class OfflinePackagingStatusResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    package_id = serializers.UUIDField(required=False)
    error = serializers.CharField(required=False)


class OfflineLicenseRevocationResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
