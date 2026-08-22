# podcasts/api/serializers/audio.py

from rest_framework import serializers
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.media.audio.models import Audio


class AudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audio
        fields = [
            "id",
            "name",
            "file",
            "master",
            "duration",
            "codec",
            "sample_rate",
            "bitrate",
            "size_bytes",
            "processed",
            "quality",
            "uploaded_at",
            "created_at",
            "prefix",
        ]
        read_only_fields = [
            "id",
            "duration",
            "codec",
            "sample_rate",
            "bitrate",
            "size_bytes",
            "processed",
            "quality",
            "uploaded_at",
            "created_at",
            "prefix",
        ]

        # write_only_fields = [
        #     "file"
        # ]

    def validate(self, attrs):
        episode = self.context.get("episode")
        master = attrs.get("master", False)

        if master:
            existing_master = Audio.objects.filter(
                episode=episode,
                master=True
            )

            if self.instance:
                existing_master = existing_master.exclude(pk=self.instance.pk)

            if existing_master.exists():
                raise serializers.ValidationError(
                    "This episode already has a master audio."
                )

        return attrs

    def create(self, validated_data):
        episode = self.context["episode"]

        return Audio.objects.create(
            episode=episode,
            **validated_data
        )

    def update(self, instance, validated_data):
        # Replace file if provided
        if "file" in validated_data and instance.file:
            instance.file.delete(save=False)

        return super().update(instance, validated_data)
