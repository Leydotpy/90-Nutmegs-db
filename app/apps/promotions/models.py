"""Promotion models for editorial modules and remote banner campaigns."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from utils.generic_relations import normalize_generic_object_id

from apps.fields import ExtendedURLField
from apps.posts.podcasts.models import Episode, Podcast


class BannerProvider(models.TextChoices):
    """External rendering services supported by the promotions domain."""

    GIFFY = "giffy", _("Giffy")


class BannerSyncStatus(models.TextChoices):
    """States used while synchronising banner rendering with Giffy."""

    DRAFT = "draft", _("Draft")
    QUEUED = "queued", _("Queued")
    PROCESSING = "processing", _("Processing")
    READY = "ready", _("Ready")
    FAILED = "failed", _("Failed")


class BannerPreset(models.TextChoices):
    """Render presets shared with the Giffy service contract."""

    STORY = "story", _("Story")
    LANDSCAPE = "landscape", _("Landscape")
    SQUARE = "square", _("Square")
    HERO = "hero", _("Hero")
    CUSTOM = "custom", _("Custom")


class BannerOutputFormat(models.TextChoices):
    """Output formats supported by the banner generation pipeline."""

    PNG = "png", _("PNG")
    JPG = "jpg", _("JPG")
    GIF = "gif", _("GIF")
    MP4 = "mp4", _("MP4")
    WEBM = "webm", _("WEBM")


class BannerPosition(models.TextChoices):
    """Preferred location for the text treatment within the banner frame."""

    AUTO = "auto", _("Auto")
    TOP = "top", _("Top")
    MIDDLE = "middle", _("Middle")
    BOTTOM = "bottom", _("Bottom")


class LinkedPromotionQuerySet(models.QuerySet):
    """Query helpers for generic linked promotions."""

    def for_object(self, instance):
        content_type = ContentType.objects.get_for_model(instance.__class__)
        object_id = normalize_generic_object_id(instance.pk)
        return self.filter(content_type=content_type, object_id=object_id)


class LinkedPromotionManager(models.Manager):
    """Manager exposing object-specific lookup helpers."""

    def get_queryset(self):
        return LinkedPromotionQuerySet(self.model, using=self._db)

    def for_object(self, instance):
        return self.get_queryset().for_object(instance)


class LinkedPromotion(models.Model):
    """Generic promotion placement that links a promotion to a page or keyword."""

    # Generic relation to any promotion subclass instance.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64, db_index=True)
    content_object = fields.GenericForeignKey()

    # Position identifies the slot where the promotion should appear.
    position = models.CharField(
        _("Position"), max_length=100, help_text=_("The position on the page.")
    )
    # Display order controls deterministic ordering inside the placement slot.
    display_order = models.PositiveIntegerField(_("Display Order"), default=0)
    # Clicks provide a lightweight engagement counter for editorial reporting.
    clicks = models.PositiveIntegerField(_("Clicks"), default=0)
    # Date created helps with operational ordering and auditing.
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    objects = LinkedPromotionManager()

    class Meta:
        abstract = True
        app_label = "promotions"
        ordering = ["-clicks"]
        verbose_name = _("Linked Promotion")
        verbose_name_plural = _("Linked Promotions")

    def record_click(self):
        """Increment the click counter atomically for engagement tracking."""
        self.clicks += 1
        self.save(update_fields=["clicks"])

    record_click.alters_data = True


class PagePromotion(LinkedPromotion):
    """Promotion placement targeting a concrete site URL."""

    page_url = ExtendedURLField(_("Page URL"), max_length=128, default="/", db_index=True)

    def __str__(self):
        return f"{self.content_object} on {self.page_url}"

    def get_link(self):
        return self.page_url

    class Meta(LinkedPromotion.Meta):
        verbose_name = _("Page Promotion")
        verbose_name_plural = _("Page Promotions")


class KeywordPromotion(LinkedPromotion):
    """Promotion placement targeting a keyword-driven discovery slot."""

    keyword = models.CharField(_("Keyword"), max_length=200)
    filter = models.CharField(_("Filter"), max_length=200, blank=True, null=True)

    def get_link(self):
        return self.keyword

    class Meta(LinkedPromotion.Meta):
        verbose_name = _("Keyword Promotion")
        verbose_name_plural = _("Keyword Promotions")


class AbstractPromotion(models.Model):
    """Base promotion model shared by image and list-style promotion modules."""

    _type = "Promotion"
    # Keywords expose the promotion in discovery contexts.
    keywords = fields.GenericRelation(KeywordPromotion, verbose_name=_("Keywords"))
    # Pages expose the promotion in page-level slots.
    pages = fields.GenericRelation(PagePromotion, verbose_name=_("Pages"))

    class Meta:
        abstract = True
        app_label = "promotions"
        verbose_name = _("Promotion")
        verbose_name_plural = _("Promotions")

    @property
    def type(self):
        return _(self._type)

    @classmethod
    def classname(cls):
        return cls.__name__.lower()

    @property
    def code(self):
        return self.__class__.__name__.lower()

    @property
    def content_type(self):
        return ContentType.objects.get_for_model(self)

    @property
    def num_times_used(self):
        object_id = normalize_generic_object_id(self.pk)
        ctype = self.content_type
        page_count = PagePromotion.objects.filter(content_type=ctype, object_id=object_id).count()
        keyword_count = KeywordPromotion.objects.filter(
            content_type=ctype, object_id=object_id
        ).count()
        return page_count + keyword_count


class ImagePromotionQuerySet(models.QuerySet):
    """Query helpers for banner-like image promotions."""

    def ready(self):
        return self.filter(banner_status=BannerSyncStatus.READY).exclude(banner_url="")

    def discoverable(self, *, now=None):
        discoverable_podcasts = Podcast.objects.discoverable(now=now).values("pk")
        return self.filter(
            models.Q(podcast__isnull=True)
            | models.Q(podcast_id__in=discoverable_podcasts)
        )

    def failed(self):
        return self.filter(banner_status=BannerSyncStatus.FAILED)

    def pending_sync(self):
        return self.filter(banner_status__in=[BannerSyncStatus.QUEUED, BannerSyncStatus.PROCESSING])

    def for_podcast(self, podcast):
        return self.filter(podcast=podcast)


class ImagePromotionManager(models.Manager):
    """Manager exposing frequently used image-promotion slices."""

    def get_queryset(self):
        return ImagePromotionQuerySet(self.model, using=self._db)

    def ready(self):
        return self.get_queryset().ready()

    def discoverable(self, *, now=None):
        return self.get_queryset().discoverable(now=now)

    def failed(self):
        return self.get_queryset().failed()

    def pending_sync(self):
        return self.get_queryset().pending_sync()

    def for_podcast(self, podcast):
        return self.get_queryset().for_podcast(podcast)


class Image(AbstractPromotion):
    """A remotely rendered banner promotion whose asset lifecycle is handled by Giffy."""

    _type = "Image"

    # Name is the internal editorial label used in dashboards and admin screens.
    name = models.CharField(_("Name"), max_length=128)
    # Podcast optionally scopes the promotion to a specific show or content family.
    podcast = models.ForeignKey(
        Podcast,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="image_promotions",
    )
    # Title is the primary headline sent to the banner renderer.
    title = models.CharField(_("Title"), max_length=255)
    # Description provides optional supporting copy for the rendered banner.
    description = models.TextField(_("Description"), blank=True)
    # CTA text renders as the action button or callout on the generated banner.
    cta_text = models.CharField(_("CTA Text"), max_length=80, blank=True)
    # Preferred colour nudges the external renderer toward a brand accent.
    preferred_color = models.CharField(_("Preferred Color"), max_length=32, blank=True)

    # Provider identifies the remote service responsible for producing the banner asset.
    banner_provider = models.CharField(
        _("Banner Provider"),
        max_length=16,
        choices=BannerProvider.choices,
        default=BannerProvider.GIFFY,
    )
    # Preset controls the aspect-ratio and layout preset used by Giffy.
    banner_preset = models.CharField(
        _("Banner Preset"),
        max_length=16,
        choices=BannerPreset.choices,
        default=BannerPreset.LANDSCAPE,
    )
    # Output format determines whether the final asset is static or animated.
    banner_output_format = models.CharField(
        _("Banner Output Format"),
        max_length=8,
        choices=BannerOutputFormat.choices,
        default=BannerOutputFormat.PNG,
    )
    # Banner position suggests where text overlays should sit inside the frame.
    banner_position = models.CharField(
        _("Banner Position"),
        max_length=16,
        choices=BannerPosition.choices,
        default=BannerPosition.AUTO,
    )
    # Width and height are stored locally so the service contract stays explicit and inspectable.
    banner_width = models.PositiveIntegerField(_("Banner Width"), default=1200)
    banner_height = models.PositiveIntegerField(_("Banner Height"), default=628)

    # Banner status reflects the latest known remote rendering state.
    banner_status = models.CharField(
        _("Banner Status"),
        max_length=16,
        choices=BannerSyncStatus.choices,
        default=BannerSyncStatus.DRAFT,
        db_index=True,
    )
    # Banner job id stores the remote Giffy job identifier for polling and callbacks.
    banner_job_id = models.UUIDField(_("Banner Job ID"), null=True, blank=True, db_index=True)
    # Banner URL stores the final rendered asset URL served back from Giffy.
    banner_url = models.URLField(_("Banner URL"), blank=True)
    # Source filename tracks the latest uploaded source asset for auditability.
    source_filename = models.CharField(_("Source Filename"), max_length=255, blank=True)
    # Source content type helps preserve the upload contract for future regenerations.
    source_content_type = models.CharField(_("Source Content Type"), max_length=120, blank=True)
    # Banner error captures the latest failure message returned by the remote service.
    banner_error = models.TextField(_("Banner Error"), blank=True)

    # Rendered at records when the remote asset successfully finished processing.
    rendered_at = models.DateTimeField(_("Rendered At"), null=True, blank=True)
    # Synced at records when this local record was last updated from the remote service.
    synced_at = models.DateTimeField(_("Synced At"), null=True, blank=True)
    # Date created and updated support operational sorting and auditing.
    date_created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = ImagePromotionManager()

    class Meta:
        verbose_name = _("Image Promotion")
        verbose_name_plural = _("Image Promotions")
        ordering = ["-date_created"]
        indexes = [
            models.Index(fields=["banner_status", "date_created"]),
            models.Index(fields=["podcast", "banner_status"]),
        ]

    def __str__(self):
        return self.name

    @property
    def resource_id(self):
        """Expose the promotion primary key as the cross-service banner resource identifier."""
        return normalize_generic_object_id(self.pk)

    @property
    def is_ready(self) -> bool:
        """Return True when the remote banner asset is ready to be shown to end users."""
        return self.banner_status == BannerSyncStatus.READY and bool(self.banner_url)

    def clean(self):
        """Validate banner dimensions before remote submission."""
        if self.banner_width < 200 or self.banner_height < 100:
            raise ValidationError("Banner dimensions are too small.")
        if self.banner_width > 4000 or self.banner_height > 4000:
            raise ValidationError("Banner dimensions are too large.")

    def get_banner_payload(self) -> dict[str, str | int]:
        """Build the canonical payload sent to the Giffy service."""
        return {
            "resource_id": str(self.resource_id),
            "title": self.title,
            "description": self.description,
            "cta_text": self.cta_text,
            "preferred_color": self.preferred_color,
            "preset": self.banner_preset,
            "width": self.banner_width,
            "height": self.banner_height,
            "output_format": self.banner_output_format,
            "banner_position": self.banner_position,
        }

    def mark_banner_submitted(
        self, *, job_id, source_filename: str = "", source_content_type: str = ""
    ):
        """Mark the promotion as successfully queued with the remote banner service."""
        self.banner_job_id = job_id
        self.banner_status = BannerSyncStatus.QUEUED
        self.banner_url = ""
        self.banner_error = ""
        self.rendered_at = None
        self.source_filename = source_filename or self.source_filename
        self.source_content_type = source_content_type or self.source_content_type
        self.synced_at = timezone.now()
        self.save(
            update_fields=[
                "banner_job_id",
                "banner_status",
                "banner_url",
                "banner_error",
                "rendered_at",
                "source_filename",
                "source_content_type",
                "synced_at",
            ]
        )

    def mark_banner_processing(self):
        """Mark the promotion as currently being processed by the remote renderer."""
        self.banner_status = BannerSyncStatus.PROCESSING
        self.synced_at = timezone.now()
        self.save(update_fields=["banner_status", "synced_at"])

    def mark_banner_ready(self, *, banner_url: str, job_id=None, rendered_at=None):
        """Persist the remote success payload onto the local promotion record."""
        if job_id:
            self.banner_job_id = job_id
        self.banner_status = BannerSyncStatus.READY
        self.banner_url = banner_url
        self.banner_error = ""
        self.rendered_at = rendered_at or timezone.now()
        self.synced_at = timezone.now()
        self.save(
            update_fields=[
                "banner_job_id",
                "banner_status",
                "banner_url",
                "banner_error",
                "rendered_at",
                "synced_at",
            ]
        )

    def mark_banner_failed(self, *, error_message: str, job_id=None):
        """Persist the latest remote failure payload for operator visibility."""
        if job_id:
            self.banner_job_id = job_id
        self.banner_status = BannerSyncStatus.FAILED
        self.banner_error = error_message
        self.synced_at = timezone.now()
        self.save(update_fields=["banner_job_id", "banner_status", "banner_error", "synced_at"])


class MultiImage(AbstractPromotion):
    """A rotating group of image promotions that can be rendered as a carousel or rotator."""

    _type = "Multi-image"
    # Name is the editorial label for the rotating banner set.
    name = models.CharField(_("Name"), max_length=128)
    # Images references the child banner promotions that participate in the rotation.
    images = models.ManyToManyField(
        Image,
        blank=True,
        help_text=_(
            "Choose the image promotions that this block will use. "
            "(You may need to create some first)."
        ),
    )
    # Date created supports admin ordering and audit trails.
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Multi Image")
        verbose_name_plural = _("Multi Images")


class AbstractPostList(AbstractPromotion):
    """Abstract superclass for promotions that present a curated list of content."""

    # Name is the visible title of the editorial list.
    name = models.CharField(pgettext_lazy("Promotion post list title", "Title"), max_length=255)
    # Subtitle gives editors a shorter supporting line for the list header.
    subtitle = models.CharField(max_length=120, null=True, blank=True)
    # Description stores the body copy for the promotion module.
    description = models.TextField(_("Description"), blank=True)
    # Link URL defines the optional destination CTA for the module.
    link_url = models.URLField(_("Link URL"), blank=True)
    # Link text defines the user-facing CTA label for the module.
    link_text = models.CharField(_("Link text"), max_length=255, blank=True)
    # Date created supports sorting and operational visibility.
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name = _("Post list")
        verbose_name_plural = _("Post lists")

    def __str__(self):
        return self.name

    def get_queryset(self, *args, **kwargs):
        raise NotImplementedError

    def get_objects(self, *args, **kwargs):
        return self.get_queryset(*args, **kwargs)


class HandPickedPostList(AbstractPostList):
    """A manually curated list of podcasts chosen by editors."""

    _type = "Post list"
    podcasts = models.ManyToManyField(
        Podcast,
        through="OrderedPodcast",
        blank=True,
        verbose_name=_("Podcasts"),
    )

    def get_queryset(self):
        return Podcast.objects.discoverable().filter(
            orderedpodcast__list=self,
        ).order_by("orderedpodcast__display_order")

    def get_ordered_podcasts(self):
        return self.get_queryset()

    class Meta:
        verbose_name = _("Hand Picked Post List")
        verbose_name_plural = _("Hand Picked Post Lists")


class OrderedPodcast(models.Model):
    """Ordering table used to keep curated podcasts in a deterministic sequence."""

    # List identifies the parent curated promotion module.
    list = models.ForeignKey(HandPickedPostList, on_delete=models.CASCADE, verbose_name=_("List"))
    # Podcast references the selected podcast inside that module.
    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE, verbose_name=_("Podcast"))
    # Display order determines the explicit editorial ordering.
    display_order = models.PositiveIntegerField(_("Display Order"), default=0)

    class Meta:
        app_label = "promotions"
        ordering = ("display_order",)
        constraints = [
            models.UniqueConstraint(
                fields=["list", "podcast"], name="unique_ordered_podcast_in_list"
            ),
        ]
        verbose_name = _("Ordered podcast")
        verbose_name_plural = _("Ordered podcast")


class AutomaticPostList(AbstractPostList):
    """A list whose contents are derived dynamically from user context or recency."""

    class Method(models.TextChoices):
        SUBSCRIPTIONS = "Subscriptions", _("Subscriptions")
        RECENTLY_ADDED = "RecentlyAdded", _("Recently added podcasts")

    _type = "Auto-product list"
    # Method defines the automatic selection strategy for the module.
    method = models.CharField(_("Method"), max_length=128, choices=Method.choices)
    # Num posts caps the size of the automatic result set.
    num_posts = models.PositiveSmallIntegerField(_("Number of Podcasts"), default=15)

    def get_queryset(self, user: User):
        """Return the current automatic episode selection for the supplied user."""
        if self.method == self.Method.RECENTLY_ADDED:
            return (
                Episode.objects.discoverable()
                .select_related("podcast")
                .order_by("-timestamp")[: self.num_posts]
            )

        if self.method == self.Method.SUBSCRIPTIONS and user.is_authenticated:
            subscribed_podcast_ids = Podcast.objects.filter(subscribers=user).values_list(
                "id", flat=True
            )
            return (
                Episode.objects.discoverable()
                .select_related("podcast")
                .filter(podcast_id__in=subscribed_podcast_ids)
                .order_by("-timestamp")[: self.num_posts]
            )

        return Episode.objects.none()

    def get_episodes(self, user: User):
        return self.get_queryset(user)

    class Meta:
        verbose_name = _("Automatic post list")
        verbose_name_plural = _("Automatic post lists")


class OrderedPostList(HandPickedPostList):
    """Legacy ordered post list variant retained for backwards compatibility."""

    display_order = models.PositiveIntegerField(_("Display Order"), default=0)

    class Meta:
        ordering = ("display_order",)
        verbose_name = _("Ordered Post List")
        verbose_name_plural = _("Ordered Post Lists")
