"""Analytics models and helpers for generic content interactions."""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from core.compat import get_user_model
from utils.generic_relations import normalize_generic_object_id
from utils.utils import get_client_ip

User = get_user_model()


class ObjectView(models.Model):
    """Raw view-event log used for popularity calculations and recommendation data."""

    # The authenticated user who viewed the object when available.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="object_views",
    )
    # A fallback identifier for anonymous viewers so repeat refreshes can be deduplicated.
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Generic relation to any content model we want to track.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64, db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")

    # The exact moment the view was recorded.
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Object View"
        verbose_name_plural = "Object Views"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "content_type"]),
            models.Index(fields=["content_type", "object_id", "ip_address", "timestamp"]),
        ]

    def __str__(self) -> str:
        viewer = self.user if self.user else self.ip_address
        return f"{viewer} viewed {self.content_object}"


class AnalyticsQueryset(models.QuerySet):
    """Base queryset placeholder for future analytics-specific helpers."""


class AnalyticsManager(models.Manager):
    """Manager exposing a dedicated queryset for analytics-enabled models."""

    def get_queryset(self):
        return AnalyticsQueryset(self.model, using=self._db)


class AbstractAnalytics(models.Model):
    """Shared analytics and taxonomy relationships for domain content models."""

    # UUID primary keys keep identifiers stable across services and shared artifacts.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    # Countries provide geopolitical context for search, filtering, and recommendation.
    countries = models.ManyToManyField("region.Country", blank=True)
    # Competitions link content to leagues and tournaments.
    competitions = models.ManyToManyField("leagues.League", blank=True)
    # Regions help group content geographically for discovery.
    regions = models.ManyToManyField("region.Region", blank=True)
    # Teams connect podcasts and episodes to clubs that fans follow.
    teams = models.ManyToManyField("clubs.Team", blank=True)
    # Players capture person-level affinity and search relationships.
    players = models.ManyToManyField("persons.Player", blank=True)
    # Matches tie content directly to fixtures or match analysis.
    matches = models.ManyToManyField("match.Match", blank=True)

    # Subscribers represent explicit user intent and are reused by recommendations.
    subscribers = models.ManyToManyField(User, blank=True)

    # View logs retain event-level analytics while view_count powers fast ranking queries.
    view_logs = GenericRelation(ObjectView)
    view_count = models.PositiveIntegerField(default=0)

    analytics = AnalyticsManager()

    class Meta:
        abstract = True

    def toggle_subscription(self, user) -> bool:
        """Toggle the given user's subscription state and return the new state."""
        if self.subscribers.filter(pk=user.pk).exists():
            self.subscribers.remove(user)
            return False
        self.subscribers.add(user)
        return True

    def record_view(self, request) -> bool:
        """Record a view once per user or IP within a short cooldown window."""
        user = request.user if request.user.is_authenticated else None
        ip_address = get_client_ip(request)
        cooldown_time = timezone.now() - timedelta(minutes=10)

        existing_view = ObjectView.objects.filter(
            content_type=ContentType.objects.get_for_model(self),
            object_id=normalize_generic_object_id(self.pk),
            timestamp__gte=cooldown_time,
        )

        if user:
            is_duplicate = existing_view.filter(user=user).exists()
        else:
            is_duplicate = existing_view.filter(ip_address=ip_address).exists()

        if is_duplicate:
            return False

        ObjectView.objects.create(
            user=user,
            ip_address=ip_address,
            content_object=self,
            object_id=normalize_generic_object_id(self.pk),
        )
        self.view_count = models.F("view_count") + 1
        self.save(update_fields=["view_count"])
        self.refresh_from_db(fields=["view_count"])
        return True

    def user_has_subscribed(self, user) -> bool:
        """Return whether the supplied authenticated user subscribes to this object."""
        if not user or not user.is_authenticated:
            return False
        return self.subscribers.filter(pk=user.pk).exists()
