"""Comment models for generic content discussion threads."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import ValidationError

from utils.generic_relations import normalize_generic_object_id

User = get_user_model()


def upload_location(instance, filename):
    """Store uploaded comment media in a user- and type-specific folder."""
    stamp = timezone.now().strftime("%H_%M_%S.%f")
    return f"comments/{instance.user.username}/{instance.comment_type}/{stamp}_{filename}"


class CommentManager(models.Manager):
    """Manager for comment roots and generic relation lookups."""

    def all(self):
        return super().filter(parent=None)

    def filter_by_instance(self, instance):
        content_type = ContentType.objects.get_for_model(instance.__class__)
        object_id = normalize_generic_object_id(instance.pk)
        return super().filter(content_type=content_type, object_id=object_id, parent=None)

    def create_by_model_type(self, model_type, object_id, comment_type, content, media, user, parent_obj=None):
        """Create a comment or reply against the supplied generic object."""
        content_type = get_object_or_404(ContentType, model=model_type)
        try:
            obj = content_type.get_object_for_this_type(id=object_id)
        except ObjectDoesNotExist:
            raise

        if comment_type == Comment.Type.TEXT and not content:
            raise ValidationError({"comment": "Please type a comment"})
        if comment_type in {Comment.Type.STICKER, Comment.Type.IMAGE} and media is None:
            raise ValidationError({"comment": "Please upload a valid media file"})

        instance = self.create(
            content=content,
            comment_type=comment_type,
            user=user,
            content_type=content_type,
            media=media,
            object_id=normalize_generic_object_id(obj.pk),
        )
        if parent_obj:
            self.filter(pk=instance.id).update(parent=parent_obj)
        return instance


class Comment(models.Model):
    """Threaded generic comment model for podcasts, episodes, and related content."""

    class Type(models.TextChoices):
        TEXT = "text", _("Text")
        IMAGE = "image", _("Image")
        STICKER = "sticker", _("Sticker")

    # The author of the comment or reply.
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Generic relation targeting the commented object.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64, db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    # Parent enables one-level or multi-level threaded conversations.
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE)
    # Content stores the comment body for text comments.
    content = models.TextField(null=True, blank=True)
    # Comment type determines whether the record carries text or uploaded media.
    comment_type = models.CharField(max_length=30, choices=Type.choices, default=Type.TEXT)
    # Media holds optional stickers or image attachments.
    media = models.FileField(upload_to=upload_location, blank=True, null=True)
    # Timestamp powers ordering and pagination.
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = CommentManager()

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["content_type", "object_id", "timestamp"]),
            models.Index(fields=["user", "timestamp"]),
        ]

    def __str__(self) -> str:
        return str(self.user.username)

    @property
    def children(self):
        """Return reply comments ordered by recency."""
        return Comment.objects.filter(parent=self)

    @property
    def is_parent(self):
        """Return True when the comment is a top-level thread root."""
        return self.parent is None

    @property
    def reply_count(self):
        """Count direct replies without materialising them."""
        return self.children.count()
