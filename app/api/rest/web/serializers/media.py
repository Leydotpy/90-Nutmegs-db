from rest_framework import serializers

from api.rest.web.serializers.thumbnails import ThumbnailModelSerializer
from apps.media.models import MediaSettings
from apps.media.images.models import Image
from apps.media.chapters.models import Chapter


class ImageModelSerializer(serializers.ModelSerializer):
    thumbnails = ThumbnailModelSerializer(read_only=True, many=True, source='get_thumbnails')
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return obj.url

    class Meta:
        model = Image
        fields = ("id", "title", "file", "url", "filename", "size", "width", "height", "thumbnails")


class ChapterModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ("title", "start_time")


class MediaSettingModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaSettings
        # Explicit is better than `__all__` here so client docs are clear
        fields = [
            'volume_level', 'playback_speed', 'skip_silence', 'skip_intro_seconds',
            'skip_outro_seconds', 'gapless_playback', 'crossfade_seconds',
            'normalize_volume', 'equalizer_preset', 'voice_boost',
            'download_over_cellular', 'auto_download_subscribed', 'download_quality',
            'streaming_quality', 'data_saver_mode', 'max_cache_size_mb',
            'cache_eviction_policy', 'show_episode_artwork', 'ui_compact_mode',
            'enable_chapters', 'remember_position_per_episode', 'default_start_position',
            'skip_on_error', 'prefer_cast_device', 'sleep_timer_seconds',
            'enable_transcripts', 'transcript_language', 'notifications_new_episode',
            'analytics_opt_in', 'extra',
        ]

    def validate_volume_level(self, value):
        if not (0 <= value <= 100):
            raise serializers.ValidationError("volume_level must be between 0 and 100")
        return value

    def validate_playback_speed(self, value):
        allowed = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        # allow any float within reasonable bounds but prefer presets
        if not (0.25 <= value <= 3.0):
            raise serializers.ValidationError("playback_speed must be between 0.25 and 3.0")
        return value

    def validate_crossfade_seconds(self, value):
        if value > 30:
            raise serializers.ValidationError("crossfade_seconds must be <= 30")
        return value

    # Optionally: field-level or object-level validation for dependent rules
    def validate(self, data):
        # if data_saver_mode is True, force streaming_quality to 'low' unless explicitly overridden
        if data.get('data_saver_mode') and data.get('streaming_quality') == 'high':
            raise serializers.ValidationError("Cannot have data_saver_mode True with streaming_quality 'high'")
        return data
