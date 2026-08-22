"""Dashboard serializers for remote image promotions."""

from __future__ import annotations

from rest_framework import serializers

from apps.posts.podcasts.models import Podcast
from apps.promotions.client import GiffyClientError, submit_image_promotion
from apps.promotions.models import BannerOutputFormat, BannerPosition, BannerPreset, Image

REMOTE_RENDER_FIELDS = {
    "title",
    "description",
    "cta_text",
    "preferred_color",
    "banner_preset",
    "banner_output_format",
    "banner_position",
    "banner_width",
    "banner_height",
}


class ImagePromotionSerializer(serializers.ModelSerializer):
    """Read serializer for the dashboard-facing promotion banner record."""

    resource_id = serializers.CharField(source="pk", read_only=True)
    podcast = serializers.PrimaryKeyRelatedField(read_only=True)
    is_ready = serializers.BooleanField(read_only=True)

    class Meta:
        model = Image
        fields = [
            "id",
            "resource_id",
            "name",
            "podcast",
            "title",
            "description",
            "cta_text",
            "preferred_color",
            "banner_provider",
            "banner_preset",
            "banner_output_format",
            "banner_position",
            "banner_width",
            "banner_height",
            "banner_status",
            "banner_job_id",
            "banner_url",
            "banner_error",
            "source_filename",
            "source_content_type",
            "rendered_at",
            "synced_at",
            "date_created",
            "updated",
            "is_ready",
        ]
        read_only_fields = [
            "id",
            "resource_id",
            "banner_provider",
            "banner_status",
            "banner_job_id",
            "banner_url",
            "banner_error",
            "source_filename",
            "source_content_type",
            "rendered_at",
            "synced_at",
            "date_created",
            "updated",
            "is_ready",
        ]


class ImagePromotionWriteSerializer(ImagePromotionSerializer):
    """Write serializer that accepts uploads and queues remote banner rendering."""

    podcast = serializers.PrimaryKeyRelatedField(queryset=Podcast.objects.all(), required=False, allow_null=True)
    file = serializers.ImageField(write_only=True, required=False, allow_null=True)
    logo = serializers.ImageField(write_only=True, required=False, allow_null=True)
    banner_preset = serializers.ChoiceField(choices=BannerPreset.choices, default=BannerPreset.LANDSCAPE)
    banner_output_format = serializers.ChoiceField(choices=BannerOutputFormat.choices, default=BannerOutputFormat.PNG)
    banner_position = serializers.ChoiceField(choices=BannerPosition.choices, default=BannerPosition.AUTO)

    class Meta(ImagePromotionSerializer.Meta):
        fields = ImagePromotionSerializer.Meta.fields + ["file", "logo"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        upload = attrs.get("file")
        if self.instance is None and upload is None:
            raise serializers.ValidationError({"file": "A source image is required when creating a promotion banner."})

        if self.instance is not None and upload is None:
            requested_render_updates = REMOTE_RENDER_FIELDS.intersection(attrs.keys())
            if requested_render_updates:
                raise serializers.ValidationError(
                    {
                        "file": (
                            "Updating rendered banner fields requires a fresh upload so Giffy can render "
                            "a matching asset."
                        )
                    }
                )
        return attrs

    def create(self, validated_data):
        upload = validated_data.pop("file")
        logo = validated_data.pop("logo", None)
        instance = Image(**validated_data)
        instance.full_clean()
        instance.save()

        try:
            submit_image_promotion(instance, media_file=upload, logo_file=logo, request=self.context.get("request"))
        except GiffyClientError as exc:
            instance.delete()
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return instance

    def update(self, instance, validated_data):
        upload = validated_data.pop("file", None)
        logo = validated_data.pop("logo", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()
        instance.save()

        if upload is not None:
            try:
                submit_image_promotion(instance, media_file=upload, logo_file=logo, request=self.context.get("request"))
            except GiffyClientError as exc:
                raise serializers.ValidationError({"detail": str(exc)}) from exc
        return instance


class GiffyJobStatusSerializer(serializers.Serializer):
    """Serializer describing a Giffy callback or polled job payload."""

    job_id = serializers.UUIDField()
    resource_id = serializers.CharField()
    status = serializers.CharField()
    progress_percent = serializers.IntegerField(required=False)
    progress_stage = serializers.CharField(required=False, allow_blank=True)
    result_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    error_message = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    finished_at = serializers.DateTimeField(required=False, allow_null=True)


class RefreshPromotionStatusSerializer(serializers.Serializer):
    """Serializer for returning the latest status after a manual refresh."""

    promotion = ImagePromotionSerializer(read_only=True)
    remote = GiffyJobStatusSerializer(read_only=True)
