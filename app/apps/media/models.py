import random
import uuid
from typing import TypeVar

from django.db import models
from django.db.models import QuerySet
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

import utils
from apps.category.models import Category
from apps.media.canonical import MediaAccessClass, MediaAsset, MediaLocation, MediaVariant
from apps.posts.models import PostReaction
from apps.media.images.models import Image
from apps.thumbnail.models import Thumbnail
from core.compat import get_user_model

now = now()
User = get_user_model()

T = TypeVar("T", bound=models.Model)


def _get_random(qs: QuerySet[T]) -> T | None:
    count = qs.count()
    if count > 0:
        return qs.all()[random.randint(0, count - 1)]
    return None


class MediaSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    autoplay = models.BooleanField(default=False)
    shuffle = models.BooleanField(default=False)
    loop = models.BooleanField(default=False)

    # Playback
    volume_level = models.PositiveSmallIntegerField(default=80)  # 0-100
    playback_speed = models.FloatField(default=1.0)
    skip_silence = models.BooleanField(default=False)
    skip_intro_seconds = models.PositiveSmallIntegerField(default=0)
    skip_outro_seconds = models.PositiveSmallIntegerField(default=0)
    gapless_playback = models.BooleanField(default=True)
    crossfade_seconds = models.PositiveSmallIntegerField(default=0)

    # Audio processing
    normalize_volume = models.BooleanField(default=True)
    equalizer_preset = models.CharField(
        max_length=32,
        choices=[
            ("flat", "Flat"),
            ("bass_boost", "Bass Boost"),
            ("vocal_boost", "Vocal Boost"),
            ("treble_boost", "Treble Boost"),
            ("custom", "Custom"),
        ],
        default="flat",
    )
    voice_boost = models.BooleanField(default=False)

    # Download / network
    download_over_cellular = models.BooleanField(default=False)
    auto_download_subscribed = models.BooleanField(default=False)
    download_quality = models.CharField(
        max_length=16,
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
        default="medium",
    )
    streaming_quality = models.CharField(
        max_length=16,
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
        default="high",
    )
    data_saver_mode = models.BooleanField(default=False)

    # Offline & caching
    max_cache_size_mb = models.PositiveIntegerField(default=512)
    cache_eviction_policy = models.CharField(
        max_length=16,
        choices=[("lru", "LRU"), ("oldest", "Oldest First"), ("manual", "Manual")],
        default="lru",
    )

    # UX / UI
    show_episode_artwork = models.BooleanField(default=True)
    ui_compact_mode = models.BooleanField(default=False)
    enable_chapters = models.BooleanField(default=True)
    remember_position_per_episode = models.BooleanField(default=True)
    default_start_position = models.CharField(
        max_length=16,
        choices=[("beginning", "Beginning"), ("resume", "Resume"), ("custom", "Custom")],
        default="resume",
    )
    skip_on_error = models.BooleanField(default=True)
    prefer_cast_device = models.CharField(max_length=64, null=True, blank=True)

    # Extras
    sleep_timer_seconds = models.PositiveIntegerField(null=True, blank=True)
    enable_transcripts = models.BooleanField(default=False)
    transcript_language = models.CharField(max_length=8, default="en")
    notifications_new_episode = models.BooleanField(default=True)
    analytics_opt_in = models.BooleanField(default=False)

    # transcription
    enable_transcription = models.BooleanField(default=True)
    transcription_provider = models.CharField(
        max_length=32, choices=(("openai", "OpenAI"), ("google", "Google")), default="openai"
    )
    transcribe_on_upload = models.BooleanField(default=False)
    max_transcription_minutes = models.PositiveIntegerField(default=90)

    # Flexible: store any additional vendor or experimental settings
    extra = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"MediaSettings({self.user})"

    def can_transcribe(self, audio_seconds):
        if not self.enable_transcription:
            return False
        if audio_seconds > self.max_transcription_minutes * 60:
            return False
        return True


class PlaylistQuerySet(models.QuerySet):
    def featured(self):
        return self.filter(featured=True)

    def for_user(self, user):
        return self.filter(user=user)


class PlaylistManager(models.Manager):
    def get_queryset(self):
        return PlaylistQuerySet(self.model, using=self._db)

    def featured(self):
        return self.get_queryset().featured()

    def for_user(self, user):
        return self.get_queryset().for_user(user)


class PlayList(models.Model):
    """"""

    name = models.CharField(max_length=120, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    slug = models.SlugField(default=uuid.uuid4, unique=True, db_index=True, blank=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="playlists"
    )
    # items = models.ManyToManyField("podcasts.Episode", blank=True)
    items = models.ManyToManyField(
        "podcasts.Episode", through="PlaylistItem", blank=True, related_name="playlists"
    )
    featured = models.BooleanField(default=False, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    categories = models.ManyToManyField(Category, related_name="playlists", blank=True)

    # optional: playlist-level impressions / followers (add if you track)
    # followers = models.ManyToManyField(Profile, related_name='followed_playlists', blank=True)

    objects = PlaylistManager()

    def __str__(self):
        return self.name if self.name else str(self.pk)

    class Meta:
        ordering = ["-featured", "-timestamp"]
        verbose_name = "Playlist"
        verbose_name_plural = "Playlists"

    def get_episodes(self) -> QuerySet:
        return self.items.all()

    def get_discoverable_episodes(self) -> QuerySet:
        """Bound public playlist serialization to editorially published episodes."""

        return self.items.discoverable()

    def get_type(self):
        return f"{self._meta.app_label}.{self.__class__.__name__}"

    def get_reactions(self):
        return PostReaction.objects.filter_by_instance(self)

    def check_is_liked(self, user):
        return self.get_reactions().filter(user=user).exists()

    def get_my_reaction(self, user):
        return self.get_reactions().filter(user=user).first()

    def get_image(self):
        image = _get_random(self.images)
        if image:
            if hasattr(image, "url"):
                return getattr(image, "url")
        return None

    @property
    def duration(self):
        episodes = self.get_discoverable_episodes()
        if not episodes.exists():
            return "00:00"
        return utils.format_duration(sum(episode.get_duration() for episode in episodes))

    def get_raw_duration(self):
        episodes = self.get_discoverable_episodes()
        if not episodes.exists():
            return 0
        return sum(episode.get_raw_duration() for episode in episodes)

    @property
    def images(self):
        return Image.objects.filter_by_instance(self)


class PlaylistItem(models.Model):
    """
    Through model to preserve ordering and metadata about episodes in a playlist.
    """

    playlist = models.ForeignKey(PlayList, on_delete=models.CASCADE, related_name="playlist_items")
    episode = models.ForeignKey("podcasts.Episode", on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("playlist", "episode")
        ordering = ["position"]
