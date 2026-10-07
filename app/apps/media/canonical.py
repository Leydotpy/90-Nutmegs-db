"""Canonical provider-neutral media identities and episode bindings."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _


class MediaAccessClass(models.TextChoices):
    """Disclosure policy attached to a provider-neutral media object."""

    PUBLIC = "public", _("Public")
    UNLISTED = "unlisted", _("Unlisted")
    PRIVATE = "private", _("Private")
    PREMIUM = "premium", _("Premium")
    EARLY_ACCESS = "early_access", _("Early access")
    AD_FREE = "ad_free", _("Ad-free")
    MEMBERS_ONLY = "members_only", _("Members only")


class MediaAsset(models.Model):
    """Canonical identity and lifecycle for one durable or managed media object."""

    if TYPE_CHECKING:
        created_by_id: object

    class MediaType(models.TextChoices):
        AUDIO = "audio", _("Audio")
        IMAGE = "image", _("Image")
        VIDEO = "video", _("Video")
        TEXT = "text", _("Text")
        BINARY = "binary", _("Binary")

    class Status(models.TextChoices):
        PENDING_UPLOAD = "pending_upload", _("Pending upload")
        UPLOADED = "uploaded", _("Uploaded")
        VALIDATING = "validating", _("Validating")
        PROCESSING = "processing", _("Processing")
        READY = "ready", _("Ready")
        FAILED = "failed", _("Failed")
        DELETED = "deleted", _("Deleted")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="media_assets",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    media_type = models.CharField(max_length=16, choices=MediaType.choices)
    access_class = models.CharField(
        max_length=16,
        choices=MediaAccessClass.choices,
        default=MediaAccessClass.PRIVATE,
    )
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.PENDING_UPLOAD,
        db_index=True,
    )
    mime_type = models.CharField(max_length=255, blank=True)
    byte_size = models.PositiveBigIntegerField(null=True, blank=True)
    checksum_algorithm = models.CharField(max_length=16, blank=True, default="sha256")
    checksum = models.CharField(max_length=128, blank=True, db_index=True)
    original_filename = models.CharField(max_length=255, blank=True)
    source_asset = models.ForeignKey(
        "self",
        related_name="derived_assets",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    storage_class = models.CharField(max_length=64, blank=True)
    processing_version = models.CharField(max_length=64, blank=True)
    upload_idempotency_key = models.CharField(max_length=128, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=("status", "created_at"),
                name="media_asset_status_created_idx",
            ),
            models.Index(
                fields=("media_type", "access_class"),
                name="media_asset_type_access_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(source_asset__isnull=True) | ~Q(id=F("source_asset_id")),
                name="media_asset_source_not_self",
            ),
            models.UniqueConstraint(
                fields=("created_by", "upload_idempotency_key"),
                condition=~Q(upload_idempotency_key="") & Q(created_by__isnull=False),
                name="media_asset_creator_idempotency_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.media_type}:{self.pk}"


class MediaLocation(models.Model):
    """Opaque provider location for an asset; never a durable signed URL."""

    if TYPE_CHECKING:
        asset_id: uuid.UUID

    class Provider(models.TextChoices):
        CLOUDFLARE = "cloudflare", _("Cloudflare")
        LEGACY_AWS = "legacy_aws", _("Legacy AWS")
        LOCAL = "local", _("Local/development")

    class Product(models.TextChoices):
        R2 = "r2", _("R2")
        IMAGES = "images", _("Images")
        STREAM = "stream", _("Stream")
        S3 = "s3", _("S3")
        FILESYSTEM = "filesystem", _("Filesystem")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        AVAILABLE = "available", _("Available")
        FAILED = "failed", _("Failed")
        DELETING = "deleting", _("Deleting")
        DELETED = "deleted", _("Deleted")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(
        MediaAsset,
        related_name="locations",
        on_delete=models.CASCADE,
    )
    provider = models.CharField(max_length=32, choices=Provider.choices)
    product = models.CharField(max_length=32, choices=Product.choices)
    locator = models.CharField(max_length=1024)
    container = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    is_primary = models.BooleanField(default=False)
    etag = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=("asset", "status"),
                name="media_loc_asset_status_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "product", "container", "locator"),
                name="media_loc_provider_object_uniq",
            ),
            models.UniqueConstraint(
                fields=("asset",),
                condition=Q(is_primary=True),
                name="media_location_one_primary_per_asset",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.provider}/{self.product}:{self.asset_id}"


class MediaVariant(models.Model):
    """Describe how an asset participates in an episode's canonical timeline."""

    if TYPE_CHECKING:
        asset_id: uuid.UUID
        episode_id: object | None

    class Kind(models.TextChoices):
        AUDIO_MASTER = "audio_master", _("Audio master")
        AUDIO_HIGH = "audio_high", _("Audio high")
        AUDIO_STANDARD = "audio_standard", _("Audio standard")
        AUDIO_DATA_SAVER = "audio_data_saver", _("Audio data saver")
        VIDEO_MASTER = "video_master", _("Video master")
        VIDEO_1080 = "video_1080", _("Video 1080p")
        VIDEO_720 = "video_720", _("Video 720p")
        VIDEO_480 = "video_480", _("Video 480p")
        VIDEO_ADAPTIVE = "video_adaptive", _("Video adaptive")
        CAPTION = "caption", _("Caption")
        THUMBNAIL = "thumbnail", _("Thumbnail")
        WAVEFORM = "waveform", _("Waveform")
        PREVIEW = "preview", _("Preview")
        OTHER = "other", _("Other")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        PROCESSING = "processing", _("Processing")
        READY = "ready", _("Ready")
        FAILED = "failed", _("Failed")
        RETIRED = "retired", _("Retired")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    episode = models.ForeignKey(
        "podcasts.Episode",
        related_name="media_variants",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    asset = models.ForeignKey(
        MediaAsset,
        related_name="variants",
        on_delete=models.PROTECT,
    )
    access_class = models.CharField(
        max_length=16,
        choices=MediaAccessClass.choices,
        blank=True,
        default="",
        help_text="Optional binding-level override; otherwise inherit from the asset.",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    codec = models.CharField(max_length=64, blank=True)
    container = models.CharField(max_length=64, blank=True)
    bitrate = models.PositiveIntegerField(null=True, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    duration_ms = models.PositiveBigIntegerField(null=True, blank=True)
    language = models.CharField(max_length=35, blank=True)
    processing_version = models.CharField(max_length=64, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=("episode", "kind", "status"),
                name="media_variant_ep_kind_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("episode", "asset", "kind"),
                condition=Q(episode__isnull=False),
                name="media_variant_episode_asset_kind_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.kind}:{self.asset_id}"

    @property
    def effective_access_class(self) -> str:
        return self.access_class or self.asset.access_class
