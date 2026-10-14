import datetime
import math
import uuid
from decimal import Decimal, InvalidOperation

import utils
from core.compat import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Count, Q, QuerySet
from django.utils import timezone
from utils.utils import get_client_ip

from apps.category.models import Category
from apps.fields.tagsfield import TagsField
from apps.media.audio.models import Audio
from apps.media.images.models import Image
from apps.memberships.models import Plan
from apps.posts.models import (
    AbstractAnalytics,
    BasePost,
    Comment,
    PostManager,
    PostQueryset,
    PostReaction,
)
from apps.posts.podcasts.utils import get_default_title

User = get_user_model()


class PodcastQuerySet(PostQueryset):
    def published(self, *, now=None):
        """Return podcasts whose explicit publication window is open."""

        now = now or timezone.now()
        return self.filter(
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at__isnull=False,
            published_at__lte=now,
        )

    def discoverable(self, *, now=None):
        """Return public root podcasts, excluding legacy child-season rows."""

        return self.published(now=now).filter(
            parent__isnull=True,
            structure__in=(Podcast.Structure.PARENT, Podcast.Structure.STANDALONE),
        )

    def recent(self):
        """Standard recent posts (last 3 days)"""
        limit = timezone.now() - datetime.timedelta(days=3)
        return self.filter(timestamp__gte=limit).order_by("-timestamp")

    def trending(self, days=3):
        """
        Sorts by 'Velocity': Number of views in the last X days.
        """
        # Calculate the date threshold
        time_threshold = timezone.now() - datetime.timedelta(days=days)

        # We query the ObjectView (view_logs) table via the GenericRelation
        return self.annotate(
            recent_view_count=Count("view_logs", filter=Q(view_logs__timestamp__gte=time_threshold))
        ).order_by("-recent_view_count", "-timestamp")

    def recommended(self, user, limit=10):
        """
        Smart recommendation engine.
        Priority 1: Podcasts matching User's Subscribed Teams/Regions/Competitions.
        Priority 2: Trending podcasts (fallback).
        """
        if not user.is_authenticated:
            # Fallback for anonymous users: Just show trending
            return self.trending()[:limit]

        # 1. Gather User's Interests (From their own AbstractAnalytics subscriptions)
        # Assuming the User model or a Profile model has these M2M relations,
        # OR we check what the user has previously subscribed to.
        # Let's assume we look at what entities the USER follows:

        # (You might need to adjust these lookups based on where you store User interests.
        # If User follows a 'Team', we want Podcasts tagged with that 'Team'.)

        # Example: Get IDs of teams/regions the user follows
        # subscribed_teams = user.following_teams.values_list('pk', flat=True)
        # subscribed_regions = user.following_regions.values_list('pk', flat=True)

        # COMPLEX QUERY: "Find podcasts that share a relationship with the user"
        # We use Q objects to construct a giant OR filter.

        # Note: This relies on how you link Users to Teams/Regions.
        # If you don't have direct User->Team links, you might use:
        # "Podcasts similar to podcasts the user has already liked/subscribed to"

        subscribed_podcasts = user.subscribed_analytics.all()  # From your AbstractAnalytics

        if not subscribed_podcasts.exists():
            return self.trending()[:limit]

        # Content-Based Filtering:
        # Find podcasts sharing a Team, Region, or Competition with
        # podcasts the listener already follows.

        return (
            self.filter(
                Q(teams__in=subscribed_podcasts.values("teams"))
                | Q(regions__in=subscribed_podcasts.values("regions"))
                | Q(competitions__in=subscribed_podcasts.values("competitions"))
            )
            .exclude(
                # Don't show me podcasts I'm already subscribed to or have seen recently
                id__in=subscribed_podcasts.values("id")
            )
            .annotate(
                # Sort by "Relevance" (how many matching tags?)
                relevance=Count("teams") + Count("regions") + Count("competitions")
            )
            .order_by("-relevance", "-timestamp")
            .distinct()[:limit]
        )

    def popular_by_category(self, category_slug):
        return (
            self.filter(categories__slug=category_slug)
            .annotate(total_views=models.F("view_count"))
            .order_by("-total_views", "-timestamp")
        )


class PodcastManager(PostManager):
    def get_queryset(self):
        return PodcastQuerySet(self.model, using=self._db)

    def published(self, *, now=None):
        return self.get_queryset().published(now=now)

    def discoverable(self, *, now=None):
        return self.get_queryset().discoverable(now=now)

    def trending(self):
        return self.get_queryset().discoverable().trending()

    def recent(self):
        return self.get_queryset().discoverable().recent()

    def recommended(self, user):
        return self.get_queryset().discoverable().recommended(user)

    def popular_by_category(self, category_slug):
        return self.get_queryset().discoverable().popular_by_category(
            category_slug=category_slug
        )


class Podcast(AbstractAnalytics, BasePost):
    class PublicationStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    # Override the legacy nullable inherited field after deterministic slug
    # reconciliation in podcasts.0003. UUID-shaped slugs preserve existing URLs
    # while guaranteeing one resolvable public identifier per podcast.
    slug = models.SlugField(default=uuid.uuid4, unique=True)
    tags = TagsField(max_length=255, null=True, blank=True)
    categories = models.ManyToManyField(Category, related_name="podcasts", blank=True)
    status = models.CharField(
        max_length=16,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
        db_index=True,
    )
    explicit_content = models.BooleanField(default=False)
    language = models.CharField(max_length=35, default="en", db_index=True)
    website_url = models.URLField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = PodcastManager()

    class Meta:
        indexes = [
            models.Index(
                fields=("status", "published_at"),
                name="podcast_public_idx",
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if not self.pk:
            return
        previous = Podcast.objects.filter(pk=self.pk).values("structure").first()
        if previous is None or previous["structure"] == self.structure:
            return
        graph_is_materialized = (
            self.children.exists()
            or self.episodes.exists()
            or self.seasons.exists()
            or Season.objects.filter(legacy_podcast=self).exists()
        )
        if graph_is_materialized:
            raise ValidationError(
                {
                    "structure": (
                        "Podcast structure cannot change after Seasons, child Podcasts, "
                        "or Episodes exist."
                    )
                }
            )

    def get_episodes(self) -> QuerySet[Episode]:
        # Legacy child-Podcast URLs remain functional during the migration by
        # resolving through the explicit Season row rather than owning a second
        # episode relationship.
        if self.is_child:
            try:
                return self.canonical_season.episodes.all()
            except Season.DoesNotExist:
                pass
        return self.episodes.all()

    def get_discoverable_episodes(self) -> QuerySet[Episode]:
        """Return only editorially published episodes for public metadata surfaces."""

        return self.get_episodes().discoverable()

    def get_images(self) -> QuerySet[Image]:
        return Image.objects.filter_by_instance(self)

    def get_seasons(self) -> QuerySet[Season]:
        """Return explicit canonical seasons in deterministic display order."""

        return self.seasons.all()

    @property
    def created_at(self):
        """Canonical name retained as an alias during timestamp migration."""

        return self.timestamp

    @property
    def updated_at(self):
        """Canonical name retained as an alias during timestamp migration."""

        return self.updated

    def get_raw_duration(self):
        episodes = self.get_discoverable_episodes()
        if not episodes.exists():
            return 0
        return sum(e.get_raw_duration() for e in episodes)

    @property
    def duration_string(self) -> str:
        """
        Calculates total duration.
        Note: If 'duration' is a DB field on Episode, use aggregate(Sum('duration'))
        for better performance. Keeping original logic structure here.
        """
        episodes = self.get_discoverable_episodes()
        if not episodes.exists():
            return "00:00"

        # Optimize: If possible, change this to database aggregation
        total_seconds = sum(e.get_duration() for e in episodes)
        # total_seconds = episodes.aggregate(Sum('duration'))['duration__sum']
        return utils.format_duration(
            total_seconds
        )  # Replace with utils.format_duration(total_seconds)

    def get_image_url(self):
        """Return the newest artwork deterministically, with the UUID as tie-breaker."""

        return self.get_images().order_by("-timestamp", "pk").first()

    def get_reactions(self):
        return PostReaction.objects.filter_by_instance(self)

    def check_is_liked(self, user):
        return self.get_reactions().filter(user=user).exists()

    def get_my_reaction(self, user):
        return self.get_reactions().filter(user=user).first()

    def get_comments(self):
        return Comment.objects.filter_by_instance(self)


class SeasonQuerySet(models.QuerySet):
    def published(self, *, now=None):
        now = now or timezone.now()
        return self.filter(
            published_at__isnull=False,
            published_at__lte=now,
            podcast__status=Podcast.PublicationStatus.PUBLISHED,
            podcast__published_at__isnull=False,
            podcast__published_at__lte=now,
            podcast__parent__isnull=True,
            podcast__structure__in=(
                Podcast.Structure.PARENT,
                Podcast.Structure.STANDALONE,
            ),
        )


class Season(models.Model):
    """Canonical season owned by one Podcast.

    ``legacy_podcast`` is a temporary, non-owning bridge to the child Podcast
    row that represented this season before the canonical migration. The child
    row is deliberately retained until route and data reconciliation completes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    podcast = models.ForeignKey(
        Podcast,
        on_delete=models.CASCADE,
        related_name="seasons",
    )
    legacy_podcast = models.OneToOneField(
        Podcast,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="canonical_season",
    )
    number = models.PositiveIntegerField(null=True, blank=True)
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=50, default=uuid.uuid4)
    description = models.TextField(null=True, blank=True)
    position = models.PositiveIntegerField(default=1)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SeasonQuerySet.as_manager()

    class Meta:
        ordering = ("position", "published_at", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("podcast", "slug"),
                name="podcast_season_slug_uniq",
            ),
            models.UniqueConstraint(
                fields=("podcast", "position"),
                name="podcast_season_position_uniq",
            ),
            models.UniqueConstraint(
                fields=("podcast", "number"),
                condition=Q(number__isnull=False),
                name="podcast_season_number_uniq",
            ),
            models.CheckConstraint(
                condition=Q(position__gte=1),
                name="podcast_season_position_positive",
            ),
            models.CheckConstraint(
                condition=Q(number__isnull=True) | Q(number__gte=1),
                name="podcast_season_number_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=("podcast", "published_at"),
                name="podcast_season_public_idx",
            ),
        ]

    def __str__(self):
        return f"{self.podcast}: {self.title}"

    def clean(self):
        super().clean()
        if self.podcast_id:
            self.validate_content_identity(podcast=self.podcast, slug=self.slug)

    def validate_content_identity(self, *, podcast, slug):
        """Validate operator edits without separating a Season from its graph.

        Direct canonical edits keep the owner and public slug stable. Legacy
        child moves use the explicit atomic bridge service, which moves the
        child, Season and Episodes together rather than validating a lone row.
        """

        errors = {}
        if podcast.parent_id is not None or podcast.structure == Podcast.Structure.CHILD:
            errors["podcast"] = "A Season must belong to a root Podcast."

        previous = Season.objects.filter(pk=self.pk).values("podcast_id", "slug").first()
        if previous is not None:
            if previous["podcast_id"] != podcast.pk:
                errors["podcast"] = (
                    "A Season's Podcast cannot be changed directly. "
                    "Move legacy seasons through their child Podcast so Episodes move with them."
                )
            if previous["slug"] != str(slug):
                errors["slug"] = "A Season's public slug cannot be changed after creation."
        if errors:
            raise ValidationError(errors)

    def get_episodes(self) -> QuerySet[Episode]:
        return self.episodes.all()

    def get_discoverable_episodes(self) -> QuerySet[Episode]:
        return self.episodes.discoverable()


class EpisodeQueryset(models.QuerySet):
    def editorially_published(self):
        """Return episodes that have passed the explicit editorial state gate."""

        return self.filter(status=Episode.PublicationStatus.PUBLISHED)

    def discoverable(self, *, now=None):
        """Return episode metadata only when its owning Podcast is published."""

        now = now or timezone.now()
        return self.editorially_published().filter(
            podcast__status=Podcast.PublicationStatus.PUBLISHED,
            podcast__published_at__isnull=False,
            podcast__published_at__lte=now,
            podcast__parent__isnull=True,
            podcast__structure__in=(
                Podcast.Structure.PARENT,
                Podcast.Structure.STANDALONE,
            ),
        )

    def publicly_available(self, *, now=None):
        """Return episodes whose canonical public window is currently open."""

        now = now or timezone.now()
        return self.discoverable(now=now).filter(
            public_available_at__isnull=False,
            public_available_at__lte=now,
        )

    def latest_in_category(self, category_slug):
        return (
            self.filter(
                models.Q(categories__slug=category_slug)
                | models.Q(podcast__categories__slug=category_slug)
            )
            .order_by("-timestamp")
            .distinct()
        )


class Episode(AbstractAnalytics):
    class PublicationStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        MEMBERS = "members", "Members"
        PLAN = "plan", "Plan"
        ENTITLEMENT = "entitlement", "Entitlement"

    class EpisodeType(models.TextChoices):
        FULL = "full", "Full"
        TRAILER = "trailer", "Trailer"
        BONUS = "bonus", "Bonus"

    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE, related_name="episodes")
    season = models.ForeignKey(
        Season,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="episodes",
    )
    description = models.TextField(null=True, blank=True)
    title = models.CharField(max_length=220, null=True, blank=True)
    subtitle = models.CharField(max_length=220, null=True, blank=True)
    slug = models.UUIDField(default=uuid.uuid4, unique=True)
    episode_number = models.PositiveIntegerField(null=True, blank=True)
    episode_type = models.CharField(
        max_length=16,
        choices=EpisodeType.choices,
        default=EpisodeType.FULL,
    )
    explicit_content = models.BooleanField(default=False)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    hosts = TagsField(max_length=220, null=True, blank=True)
    tags = TagsField(max_length=255, null=True, blank=True)

    public_release_date = models.DateTimeField(null=True, blank=True)
    exclusive = models.BooleanField(
        default=False, help_text="If True, only paying plans (Fan+) can access after release"
    )
    early_access_hours = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="If set overrides plan early access hours"
    )

    # Canonical publication/access fields. The legacy release/category fields above
    # remain temporarily for expand/backfill/switch compatibility.
    status = models.CharField(
        max_length=16,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
        db_index=True,
    )
    visibility = models.CharField(
        max_length=16,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        db_index=True,
    )
    premium_available_at = models.DateTimeField(null=True, blank=True)
    public_available_at = models.DateTimeField(null=True, blank=True)
    required_plan = models.ForeignKey(
        Plan,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="required_episodes",
    )
    preview_duration_seconds = models.PositiveIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # new denormalized / precomputed field for fast ranking
    trend_score = models.FloatField(default=0.0, db_index=True)

    # optional categories per episode (useful if you tag individual episodes)
    categories = models.ManyToManyField(Category, related_name="episodes", blank=True)

    objects = EpisodeQueryset.as_manager()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Episode"
        verbose_name_plural = "Episodes"
        ordering = ("-published_at", "-timestamp")
        indexes = [
            models.Index(
                fields=("status", "public_available_at"),
                name="podcast_ep_public_idx",
            ),
            models.Index(
                fields=("status", "visibility", "premium_available_at"),
                name="podcast_ep_access_idx",
            ),
            models.Index(
                fields=("podcast", "season", "published_at"),
                name="podcast_ep_timeline_idx",
            ),
        ]

    @property
    def images(self) -> QuerySet[Image]:
        return Image.objects.filter_by_instance(self)

    @property
    def audio_qs(self) -> QuerySet[Audio]:
        return self.audios.all()

    @property
    def category_qs(self) -> QuerySet[Category]:
        return Category.objects.filter(Q(episodes=self) | Q(podcasts=self.podcast)).distinct()

    @property
    def audio(self):
        return self.audios.filter(master=True).first()

    def in_queue(self, request) -> bool:
        return request.queue.tracks.filter(track_id=self.pk).exists()

    def get_reactions(self):
        return PostReaction.objects.filter_by_instance(self)

    def check_is_liked(self, user):
        return self.get_reactions().filter(user=user).exists()

    def get_my_reaction(self, user):
        return self.get_reactions().filter(user=user).first()

    def get_comments(self):
        return Comment.objects.filter_by_instance(self)

    def get_image(self):
        return self.images.order_by("-timestamp", "pk").first()

    def get_type(self):
        return f"{self._meta.app_label}.{self.__class__.__name__}"

    def get_duration(self):
        if self.audio:
            return float(self.audio.duration)
        return 0

    def get_raw_duration(self):
        if self.audio:
            return round(self.audio.duration)
        return 0

    @property
    def duration(self):
        return utils.format_duration(self.get_duration())

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = get_default_title(self)

        if self.season_id and self.podcast_id != self.season.podcast_id:
            raise ValueError("episode.podcast must match episode.season.podcast")

        super().save(*args, **kwargs)

    def is_downloadable_by(self, user):
        """Compatibility Boolean delegated to the canonical DOWNLOAD action."""

        from apps.memberships.access import AccessService
        from apps.memberships.policies import AccessAction

        return AccessService.get_instance().has_access(
            user,
            self,
            action=AccessAction.DOWNLOAD,
        )

    def available_for(self, *, plan: Plan = None, now=None):
        """Compatibility plan check delegated to the canonical policy rules."""

        from apps.memberships.policies import access_policy

        return access_policy.plan_allows_stream(
            resource=self,
            plan=plan,
            now=now,
        )

    def get_audio_quality(self, quality):
        audio = self.audios.filter(quality=quality).first()
        if audio:
            return audio.file.url
        return self.audios.order_by("bitrate").last().file.url


class PlayBackManager(models.Manager):
    def get_recently_played(self, request):
        qs = self.get_queryset()
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            qs = qs.filter(user=user)
        else:
            ip_address = get_client_ip(request)
            if not ip_address:
                return qs.none()
            qs = qs.filter(user__isnull=True, ip_address=ip_address)
        return (
            qs.filter(
                episode__status=Episode.PublicationStatus.PUBLISHED,
                episode__podcast__status=Podcast.PublicationStatus.PUBLISHED,
                episode__podcast__published_at__isnull=False,
                episode__podcast__published_at__lte=timezone.now(),
                episode__podcast__parent__isnull=True,
                episode__podcast__structure__in=(
                    Podcast.Structure.PARENT,
                    Podcast.Structure.STANDALONE,
                ),
            )
            .select_related("episode")
            .order_by("-last_played_at")
        )

    def get_uncompleted(self, request, limit=10):
        return self.get_recently_played(request).filter(is_completed=False)[:limit]

    def update_progress(self, user, episode_id, ip_address, seconds, is_completed=False):
        """Record one checkpoint against exactly one listener identity.

        ``is_completed`` remains in the signature for API compatibility, but it
        is not authoritative. Completion is derived from the persisted master
        duration and a 90% threshold until the richer PlaybackProgress schema
        can record duration snapshots and verified end events.
        """

        try:
            numeric_seconds = Decimal(str(seconds))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("seconds must be an integer") from exc
        if (
            not numeric_seconds.is_finite()
            or numeric_seconds != numeric_seconds.to_integral_value()
        ):
            raise ValueError("seconds must be an integer")
        seconds = int(numeric_seconds)
        if seconds < 0:
            raise ValueError("seconds cannot be negative")

        duration = (
            Audio.objects.filter(
                episode_id=episode_id,
                master=True,
                duration__gt=0,
            )
            .values_list("duration", flat=True)
            .first()
        )
        if duration is not None:
            seconds = min(seconds, duration)
            threshold = math.ceil(duration * 0.9)
            threshold_completed = seconds >= threshold
        else:
            threshold_completed = False

        authenticated = bool(user is not None and getattr(user, "is_authenticated", False))
        lookup = {"episode_id": episode_id}
        create_values = {}
        if authenticated:
            lookup["user"] = user
            create_values["ip_address"] = ip_address
        else:
            if not ip_address:
                raise ValueError("an anonymous playback identity requires an IP address")
            lookup.update(user=None, ip_address=ip_address)

        # Row locking protects updates to an existing checkpoint. The current
        # schema still lacks an anonymous identity uniqueness constraint, which
        # is intentionally deferred to the canonical playback migration.
        with transaction.atomic(using=self.db):
            progress = self.select_for_update().filter(**lookup).first()
            if progress is None:
                progress = self.model(
                    **lookup,
                    **create_values,
                    current_timestamp=seconds,
                    is_completed=threshold_completed,
                )
            else:
                progress.current_timestamp = seconds
                progress.ip_address = ip_address
                progress.is_completed = progress.is_completed or threshold_completed
            progress.save(using=self.db)
        return progress


class PlayBack(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="playback_history"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    current_timestamp = models.IntegerField(default=0, help_text="Seconds Played")
    is_completed = models.BooleanField(default=False)
    last_played_at = models.DateTimeField(auto_now=True)

    objects = PlayBackManager()

    class Meta:
        unique_together = ("user", "episode")
        ordering = ["-last_played_at"]
        verbose_name_plural = "PlayBack"

    def __str__(self):
        return f"{self.user} - {self.episode.title} ({self.current_timestamp}s)"

    def get_percentage_completed(self):
        if self.episode.get_duration() > 0:
            return round((self.current_timestamp / self.episode.get_raw_duration()) * 100)
        return 0

    def get_remaining_minutes(self):
        return round(self.episode.get_raw_duration() - self.current_timestamp)


class Summary(models.Model):
    episode = models.OneToOneField(Episode, on_delete=models.CASCADE, related_name="summary")
    summary_text = models.TextField()
    model = models.CharField(max_length=64)  # model used for summary
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"summary-{self.episode.title}"
