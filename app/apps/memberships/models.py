import datetime
import uuid
from typing import Optional

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.fields import AutoSlugField

User = settings.AUTH_USER_MODEL


class AddOn(models.Model):
    """One-off or recurring add-ons that can be purchased in addition to a plan.
    Examples: credits pack, single exclusive episode, merch voucher, one-off coaching session.
    """
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_recurring = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Entitlement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='entitlements')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')

    granted_by_subscription = models.ForeignKey('Subscription', null=True, blank=True, on_delete=models.SET_NULL)
    # granted_by_purchase = models.ForeignKey('billing.Transaction', null=True, blank=True, on_delete=models.SET_NULL)

    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['expires_at']),
        ]

        # Optionally enforce uniqueness per business rule:
        unique_together = ('user', 'content_type', 'object_id')

    def is_valid(self):
        if self.revoked:
            return False
        if self.expires_at and timezone.now() >= self.expires_at:
            return False
        return True

    def revoke(self, reason: str = None):
        self.revoked = True
        if reason:
            self.notes = (self.notes or "") + f"\nRevoked: {reason}"
        self.save(update_fields=["revoked", "notes"])


class Feature(models.Model):
    class Kind(models.TextChoices):
        EXCLUSIVE = "exclusive", _("Exclusive - Allow Access to Exclusive Episodes")
        EARLY_ACCESS = "early_access", _("Early Access - Allow Early Access to Episodes")
        TRANSCRIPTION = "allow_transcription", _("Transcriptions - Allow Transcription of Episodes")
        DOWNLOADABLE = "downloadable", _("Downloadable - Allow Offline Download of Episodes")
        PRIVATE_RSS = "private_rss", _("Private RSS - Allow Private RSS Feed for Podcatchers")
        LIVE_QNA = "live_qna", _("Access to Live Q&A Events")
        VIP_EVENTS = "vip_events", _("Access to VIP Events")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_index=True, editable=False)
    kind = models.CharField(max_length=80, choices=Kind.choices)
    slug = AutoSlugField(max_length=80, unique=True, populate_from=("kind", "id"))
    description = models.TextField(blank=True)
    is_content_feature = models.BooleanField(default=False,
                                              help_text="Set to True for features that gate content (e.g. 'Exclusive Episodes')")
    early_access_hours = models.PositiveSmallIntegerField(default=0,
                                                          help_text="Hours before public release the plan gets episodes")
    seats_limited = models.BooleanField(default=False)
    seats = models.PositiveIntegerField(null=True, blank=True,
                                        help_text='Optional seat limit for limited/insider plans')

    transcription_monthly_minutes = models.PositiveIntegerField(default=0)  # minutes included per month

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.kind


class Plan(models.Model):
    class Level(models.IntegerChoices):
        FREE = 0, _("Free")
        FAN = 1, _("Fan")
        PRO = 2, _("Pro")
        INSIDER = 3, _("Insider")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_index=True, editable=False)
    name = models.CharField(max_length=220)
    features = models.ManyToManyField(Feature, through="PlanFeature", through_fields=("plan", "feature"), blank=True)
    tier = models.PositiveSmallIntegerField(choices=Level.choices, default=Level.FREE, db_index=True)

    price_monthly = models.DecimalField(help_text="Monthly price to pay for this tier", default=0.00, decimal_places=2,
                                        max_digits=6)
    price_annual = models.DecimalField(help_text="Annual price to pay for this tier", default=0.00, decimal_places=2,
                                       max_digits=6)

    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        db_table = "plan"
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
        ordering = ("tier",)

    def has_feature(self, kind: Feature.Kind):
        return self.features.filter(kind=kind).exists()

    def grants(self, *kinds):
        return self.features.filter(kind__in=kinds).exists()

    def get_feature(self, kind: Feature.Kind) -> Feature | None:
        try:
            return self.features.filter(kind=kind).first()
        except Feature.DoesNotExist:
            return None

    def has_early_access(self):
        return self.has_feature(Feature.Kind.EARLY_ACCESS)

    def get_early_access_hours(self, effective_early_hours):
        feature = self.get_feature(Feature.Kind.EARLY_ACCESS)
        return max(effective_early_hours, feature.early_access_hours or 0)

    def get_transcription_quota(self):
        if not self.has_feature(Feature.Kind.TRANSCRIPTION):
            return 0
        return (self.features.filter(Feature.Kind.TRANSCRIPTION).first()).transcription_monthly_minutes

    def ranks_above(self, other: Plan):
        return self.tier >= other.tier

    @property
    def can_download(self):
        return self.has_feature(Feature.Kind.DOWNLOADABLE)




class PlanFeature(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('plan', 'feature')


class Membership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_index=True, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE)
    customer_id = models.UUIDField(max_length=240, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(
        Plan, on_delete=models.SET_NULL, null=True)

    objects = models.Manager()

    def __str__(self):
        return str(self.user)


class SubscriptionManager(models.Manager):
    def active_for_user(self, user):
        if not user or not user.is_authenticated:
            return self.none()
        now = timezone.now()
        # A canceled row with a future end date is a durable
        # cancel-at-period-end state and remains paid through that boundary.
        return self.filter(membership__user=user).filter(
            models.Q(
                status=Subscription.Status.ACTIVE,
                end_date__isnull=True,
            )
            | models.Q(
                status=Subscription.Status.ACTIVE,
                end_date__gt=now,
            )
            | models.Q(
                status=Subscription.Status.CANCELED,
                end_date__gt=now,
            )
        )


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        TRIAL = "trial", _("Trial")
        PAST_DUE = "past_due", _("Past due")
        CANCELED = "canceled", _("Canceled")
        EXPIRED = "expired", _("Expired")

    membership = models.ForeignKey(
        Membership, on_delete=models.CASCADE, related_name='subscriptions')
    subscription_id = models.CharField(max_length=240)
    active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL)

    start_date = models.DateTimeField(default=timezone.now)
    trial_ends = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    # Payment / provider references
    external_id = models.CharField(max_length=255, blank=True, null=True,
                                   help_text='Payment provider subscription id e.g. Stripe/Paystack')

    auto_renew = models.BooleanField(default=True)

    objects = SubscriptionManager()

    def __str__(self):
        return str(self.membership)

    class Meta:
        indexes = [models.Index(fields=['membership', 'status'])]

    def is_active(self) -> bool:
        now = timezone.now()
        if self.status == Subscription.Status.ACTIVE:
            return self.end_date is None or self.end_date > now
        if self.status == Subscription.Status.CANCELED:
            return bool(self.end_date and self.end_date > now)
        return False

    def cancel(self, when: Optional[datetime.datetime] = None):
        """Persist a replay-safe cancellation using existing durable fields.

        Renewing subscriptions become ``CANCELED`` but retain a future
        ``end_date`` as their paid-through boundary. A fixed-term ACTIVE row
        (``auto_renew=False``) is distinguishable from that scheduled state and
        cancels immediately, replacing its natural end with ``when``/now.
        """
        if self.pk is None:
            raise ValueError("A subscription must be saved before it can be canceled.")

        with transaction.atomic():
            current = (
                Subscription.objects.select_for_update()
                .only("status", "active", "auto_renew", "end_date")
                .get(pk=self.pk)
            )
            self.status = current.status
            self.active = current.active
            self.auto_renew = current.auto_renew
            self.end_date = current.end_date
            if current.status in {self.Status.CANCELED, self.Status.EXPIRED}:
                return self

            effective_end = when or timezone.now()
            current.status = Subscription.Status.CANCELED
            current.end_date = effective_end
            if current.auto_renew:
                # CANCELED + future end_date is the durable scheduled state.
                # The canonical access policy continues access through it.
                current.auto_renew = False
                update_fields = ["status", "auto_renew", "end_date"]
            else:
                # ACTIVE + non-renewing is a natural fixed-term state. Its
                # cancellation takes effect at ``effective_end`` immediately.
                update_fields = ["status", "end_date"]
            current.save(update_fields=update_fields)
            self.status = current.status
            self.active = current.active
            self.auto_renew = current.auto_renew
            self.end_date = current.end_date
        return self
