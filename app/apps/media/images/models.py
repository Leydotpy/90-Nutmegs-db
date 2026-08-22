"""Generic image asset models used across podcasts, regions, and other content."""

from __future__ import annotations

import uuid
from pathlib import Path

from PIL import Image as PillowImage
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from apps.thumbnail.models import Thumbnail
from utils.generic_relations import normalize_generic_object_id


def not_null(value):
    """Return True when the provided metadata value is meaningfully populated."""
    return value is not None and value != ""


def media_upload_location(instance, filename):
    """Build a timestamped storage key for uploaded images."""
    content_type = getattr(instance, "content_type", None)
    scope = content_type.model if content_type else instance.__class__.__name__.lower()
    stamp = timezone.now().strftime("%H%M%S.%f")
    safe_name = Path(filename).name
    return f"images/{scope}/{stamp}-{safe_name}"


class ImageQuerySet(models.QuerySet):
    """Query helpers for generic image attachments."""

    def for_instance(self, instance):
        content_type = ContentType.objects.get_for_model(instance.__class__)
        object_id = normalize_generic_object_id(instance.pk)
        return self.filter(content_type=content_type, object_id=object_id)

    def with_file(self):
        return self.exclude(file="")


class ImageManager(models.Manager):
    """Manager exposing reusable attachment helpers."""

    def get_queryset(self):
        return ImageQuerySet(self.model, using=self._db)

    def filter_by_instance(self, instance):
        return self.get_queryset().for_instance(instance)

    def create_for_model(self, ct, oid, **kwargs):
        content_type = ContentType.objects.get_for_model(ct)
        return self.create(
            content_type=content_type,
            object_id=normalize_generic_object_id(oid),
            **kwargs,
        )


class Image(models.Model):
    """A generic image attachment that can be linked to any domain model."""

    # UUIDs keep image identifiers portable across services and clients.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    # Title gives editors and the frontend a human-readable label.
    title = models.CharField(max_length=100, null=True, blank=True)
    # File stores the original uploaded image asset.
    file = models.ImageField(upload_to=media_upload_location, null=True, blank=True)
    # Generic relation components connect the image to any supported model.
    object_id = models.CharField(max_length=64, db_index=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    content_object = GenericForeignKey("content_type", "object_id")
    # Cached metadata speeds list views and frontend layout calculations.
    filename = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    size = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)

    objects = ImageManager()

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["content_type", "object_id", "timestamp"]),
        ]

    def __str__(self):
        return self.title or f"image-{self.pk}"

    def get_thumbnails(self):
        """Return generated thumbnails for this image asset."""
        return Thumbnail.objects.filter_by_instance(self)

    def sync_file_metadata(self):
        """Populate denormalised file metadata from the stored image."""
        if not self.file:
            self.filename = ""
            self.size = None
            self.width = None
            self.height = None
            return

        self.filename = Path(self.file.name).name

        try:
            self.size = self.file.size
        except Exception:
            self.size = None

        try:
            with self.file.open("rb"):
                with PillowImage.open(self.file) as image:
                    self.width, self.height = image.size
        except Exception:
            self.width = None
            self.height = None

    @property
    def has_properties(self):
        """Return True when cached metadata is complete enough for the frontend."""
        return all([not_null(self.size), not_null(self.width), not_null(self.height), not_null(self.filename)])

    @property
    def url(self):
        """Expose the file URL directly when an asset exists."""
        if not self.file:
            return None
        return self.file.url

    def save(self, *args, **kwargs):
        """Keep cached file metadata in sync before persisting the record."""
        self.object_id = normalize_generic_object_id(self.object_id)
        self.sync_file_metadata()
        super().save(*args, **kwargs)
