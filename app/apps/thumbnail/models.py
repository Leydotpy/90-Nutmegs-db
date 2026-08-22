"""Thumbnail models for media objects attached through generic relations."""

from __future__ import annotations

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.generic_relations import normalize_generic_object_id


def thumbnail_upload_to(instance, filename):
    """Generate a deterministic thumbnail storage path per source object and size."""
    folder = normalize_generic_object_id(instance.content_object.pk)
    return f"{folder}/{instance.type}/{filename}"


class ThumbnailQuerySet(models.QuerySet):
    """Query helpers for thumbnail lookups."""

    def by_instance(self, instance):
        content_type = ContentType.objects.get_for_model(instance.__class__)
        object_id = normalize_generic_object_id(instance.pk)
        return self.filter(content_type=content_type, object_id=object_id)


class ThumbnailManager(models.Manager):
    """Manager exposing thumbnail existence and lookup helpers."""

    @property
    def _queryset(self):
        return ThumbnailQuerySet(model=self.model, using=self._db)

    def filter_by_instance(self, instance):
        return self._queryset.by_instance(instance=instance)

    def exist(self, instance):
        return self.filter_by_instance(instance=instance).exists()


class Thumbnail(models.Model):
    """Generated thumbnail derivative for a generic media object."""

    class Size(models.TextChoices):
        XL = "xl", _("XL")
        LG = "lg", _("LG")
        MD = "md", _("MD")
        SM = "sm", _("SM")
        XS = "xs", _("XS")

    # Generic relation back to the parent media object.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64, db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    # Type identifies the generated thumbnail variant.
    type = models.CharField(max_length=2, choices=Size.choices, default=Size.MD)
    # Width and height are persisted for frontend layout hints.
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    # Media stores the thumbnail asset itself.
    media = models.ImageField(
        width_field="width",
        height_field="height",
        blank=True,
        null=True,
        upload_to=thumbnail_upload_to,
    )
    # Timestamp helps with ordering and invalidation.
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = ThumbnailManager()

    class Meta:
        indexes = [models.Index(fields=["content_type", "object_id", "type"])]

    def __str__(self) -> str:
        return self.media.name if self.media else f"thumbnail-{self.pk}"

    def get_absolute_url(self, request):
        """Build an absolute URL for clients that need a fully-qualified asset path."""
        return request.build_absolute_uri(self.media.url)
