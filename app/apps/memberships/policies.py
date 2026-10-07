"""Canonical server-side authorization decisions for protected resources.

This module is the single owner of episode access rules.  Existing model and
service helpers may delegate here during migration, but must not reproduce the
decision tree. Category tiers are consulted only by the one-time migration and
legacy dashboard compatibility service; live authorization reads the Episode's
explicit canonical fields.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, replace
from enum import StrEnum

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from .models import Entitlement, Feature, Plan, Subscription


class AccessAction(StrEnum):
    VIEW_METADATA = "view_metadata"
    STREAM = "stream"
    DOWNLOAD = "download"
    VIEW_TRANSCRIPT = "view_transcript"
    COMMENT = "comment"
    EARLY_ACCESS = "early_access"


class AccessReason(StrEnum):
    PUBLIC = "public"
    STAFF_BYPASS = "staff_bypass"
    ACTIVE_PLAN = "active_plan"
    ENTITLEMENT = "entitlement"
    EARLY_ACCESS = "early_access"
    REQUIRES_LOGIN = "requires_login"
    REQUIRES_PLAN = "requires_plan"
    NOT_YET_RELEASED = "not_yet_released"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class AccessDecision:
    """Structured result returned by every canonical authorization check."""

    allowed: bool
    reason: AccessReason
    required_plan: Plan | None = None
    preview_allowed: bool = False
    effective_subscription: Subscription | None = None
    effective_entitlement: Entitlement | None = None
    expires_at: datetime.datetime | None = None
    action: AccessAction | None = None
    resource_label: str = ""
    resource_id: str = ""
    principal_id: str = ""
    media_variant_id: str = ""
    media_access_class: str = ""


class AccessPolicy:
    """Evaluate resource access from durable subscription and entitlement state.

    Decisions are deterministic for the supplied ``now`` and fail closed.  The
    evaluator performs no writes and owns no commercial state.  A short-lived
    cache may wrap it, but cache state is never an authorization source.
    """

    VERSION = "access-policy-v1"

    _PUBLIC_ACTIONS = {
        AccessAction.STREAM,
        AccessAction.VIEW_TRANSCRIPT,
        AccessAction.EARLY_ACCESS,
    }
    _DIRECT_ENTITLEMENT_ACTIONS = {
        AccessAction.STREAM,
        AccessAction.VIEW_TRANSCRIPT,
        AccessAction.COMMENT,
    }
    _PLAN_MEDIA_ACCESS = frozenset({"premium", "ad_free", "members_only"})
    _PUBLIC_MEDIA_ACCESS = frozenset({"public", "unlisted"})
    _PUBLISHED_STATUS = "published"
    _PUBLIC_VISIBILITY = "public"
    _MEMBERS_VISIBILITY = "members"
    _PLAN_VISIBILITY = "plan"
    _ENTITLEMENT_VISIBILITY = "entitlement"

    def plan_allows_stream(self, *, resource, plan: Plan | None, now=None) -> bool:
        """Compatibility bridge for callers that only have a Plan, not a User.

        This owns the same rule used by ``evaluate`` and exists solely while
        legacy model APIs are being migrated to structured decisions.
        """

        now = now or timezone.now()
        if plan is None:
            return self._is_public(resource, now)
        allowed, _ = self._plan_allows(
            resource=resource,
            plan=plan,
            required_plan=self._required_plan(resource),
            now=now,
        )
        return allowed

    def evaluate(self, *, user, resource, action: AccessAction, now=None) -> AccessDecision:
        """Return the authoritative decision for ``user/resource/action``.

        ``resource`` is currently expected to be an Episode-like Django model.
        Generic direct entitlements remain supported for compatibility.  An
        unsupported or incomplete object is never treated as public.
        """

        action = AccessAction(action)
        now = now or timezone.now()
        resource_meta = getattr(resource, "_meta", None)
        resource_label = getattr(resource_meta, "label_lower", "")
        resource_id = str(getattr(resource, "pk", ""))
        principal_id = str(user.pk) if user and getattr(user, "is_authenticated", False) else ""

        def decision(**values) -> AccessDecision:
            return AccessDecision(
                action=action,
                resource_label=resource_label,
                resource_id=resource_id,
                principal_id=principal_id,
                **values,
            )

        required_plan = self._required_plan(resource)
        preview_allowed = (
            self._preview_available(resource)
            if action == AccessAction.STREAM and self._is_editorially_published(resource, now=now)
            else False
        )

        if self._is_staff(user):
            return decision(
                allowed=True,
                reason=AccessReason.STAFF_BYPASS,
                required_plan=required_plan,
                preview_allowed=preview_allowed,
            )

        if not self._is_editorially_published(resource, now=now):
            return decision(
                allowed=False,
                reason=AccessReason.NOT_YET_RELEASED,
                required_plan=required_plan,
                preview_allowed=False,
            )

        # Premium episode metadata is intentionally discoverable; media access
        # remains a separate action and decision. Draft/archived metadata was
        # rejected by the editorial-state gate above.
        if action == AccessAction.VIEW_METADATA:
            return decision(
                allowed=True,
                reason=AccessReason.PUBLIC,
                required_plan=required_plan,
                preview_allowed=preview_allowed,
            )

        is_public = self._is_public(resource, now)
        if is_public and action in self._PUBLIC_ACTIONS:
            return decision(
                allowed=True,
                reason=AccessReason.PUBLIC,
                required_plan=required_plan,
                preview_allowed=preview_allowed,
            )

        if not self._is_authenticated(user):
            return decision(
                allowed=False,
                reason=AccessReason.REQUIRES_LOGIN,
                required_plan=required_plan,
                preview_allowed=preview_allowed,
            )

        # Commenting always requires identity, even when the underlying episode
        # is public.
        if is_public and action == AccessAction.COMMENT:
            return decision(
                allowed=True,
                reason=AccessReason.PUBLIC,
                required_plan=required_plan,
            )

        direct_entitlement, entitlement_failure = self._direct_entitlement(user, resource, now)
        current_subscription, had_subscription = self._current_subscription(user, now)
        plan_entitlements = self._plan_entitlements(user, now)

        if direct_entitlement is not None and action in self._DIRECT_ENTITLEMENT_ACTIONS:
            return decision(
                allowed=True,
                reason=AccessReason.ENTITLEMENT,
                required_plan=required_plan,
                preview_allowed=preview_allowed,
                effective_entitlement=direct_entitlement,
                expires_at=direct_entitlement.expires_at,
            )

        candidates: list[tuple[Plan, Subscription | None, Entitlement | None]] = []
        if current_subscription and current_subscription.membership.plan:
            candidates.append((current_subscription.membership.plan, current_subscription, None))
        candidates.extend((plan, None, ent) for ent, plan in plan_entitlements)
        candidates.sort(key=lambda item: item[0].tier, reverse=True)

        denial_reason = AccessReason.REQUIRES_PLAN
        for plan, subscription, plan_entitlement in candidates:
            if action == AccessAction.DOWNLOAD and not plan.has_feature(Feature.Kind.DOWNLOADABLE):
                continue

            plan_allowed, plan_reason = self._plan_allows(
                resource=resource,
                plan=plan,
                required_plan=required_plan,
                now=now,
            )

            if not plan_allowed:
                if plan_reason == AccessReason.NOT_YET_RELEASED:
                    denial_reason = plan_reason
                continue

            if action == AccessAction.EARLY_ACCESS and plan_reason != AccessReason.EARLY_ACCESS:
                # The resource is not inside an early-access window; ordinary
                # plan access must not be relabelled as this capability.
                continue

            reason = plan_reason
            if plan_entitlement is not None and reason != AccessReason.EARLY_ACCESS:
                reason = AccessReason.ENTITLEMENT
            return decision(
                allowed=True,
                reason=reason,
                required_plan=required_plan,
                preview_allowed=preview_allowed,
                effective_subscription=subscription,
                effective_entitlement=plan_entitlement,
                expires_at=self._candidate_expiry(subscription, plan_entitlement),
            )

        if entitlement_failure is not None:
            denial_reason = entitlement_failure
        elif had_subscription and current_subscription is None:
            denial_reason = AccessReason.EXPIRED
        elif self._release_is_future(resource, now):
            denial_reason = AccessReason.NOT_YET_RELEASED

        return decision(
            allowed=False,
            reason=denial_reason,
            required_plan=required_plan,
            preview_allowed=preview_allowed,
        )

    def evaluate_media(
        self,
        *,
        user,
        resource,
        variant,
        action: AccessAction,
        now=None,
    ) -> AccessDecision:
        """Evaluate an episode action and bind it to one exact ready media variant.

        The transitional episode policy can grant protected variants only when its
        decision already proves staff, entitlement, plan, or early-access authority.
        A released episode short-circuits the base policy as public, so plan-gated
        variants perform one additional current paid-plan/entitlement check.
        """

        now = now or timezone.now()
        base = self.evaluate(user=user, resource=resource, action=action, now=now)
        variant_id = str(getattr(variant, "pk", ""))
        access_class = str(getattr(variant, "effective_access_class", ""))
        belongs_to_resource = getattr(variant, "episode_id", None) == getattr(resource, "pk", None)
        ready = (
            getattr(variant, "status", None) == "ready"
            and getattr(
                getattr(variant, "asset", None),
                "status",
                None,
            )
            == "ready"
        )

        if (
            access_class in self._PLAN_MEDIA_ACCESS
            and base.allowed
            and base.reason == AccessReason.PUBLIC
        ):
            base = self._resolve_paid_media_grant(
                base=base,
                user=user,
                resource=resource,
                now=now,
            )

        scope_allowed = False
        if access_class in self._PUBLIC_MEDIA_ACCESS:
            scope_allowed = base.allowed
        elif access_class == "private":
            scope_allowed = base.allowed and base.reason in {
                AccessReason.STAFF_BYPASS,
                AccessReason.ENTITLEMENT,
            }
        elif access_class in self._PLAN_MEDIA_ACCESS:
            scope_allowed = base.allowed and base.reason in {
                AccessReason.STAFF_BYPASS,
                AccessReason.ACTIVE_PLAN,
                AccessReason.ENTITLEMENT,
            }
        elif access_class == "early_access":
            scope_allowed = base.allowed and base.reason in {
                AccessReason.STAFF_BYPASS,
                AccessReason.EARLY_ACCESS,
                AccessReason.ENTITLEMENT,
            }

        allowed = bool(variant_id and belongs_to_resource and ready and scope_allowed)
        reason = base.reason if allowed or not base.allowed else AccessReason.REQUIRES_PLAN
        return replace(
            base,
            allowed=allowed,
            reason=reason,
            media_variant_id=variant_id,
            media_access_class=access_class,
        )

    def _resolve_paid_media_grant(
        self,
        *,
        base: AccessDecision,
        user,
        resource,
        now,
    ) -> AccessDecision:
        """Replace a public episode grant only when paid media authority is current."""

        if not self._is_authenticated(user):
            return base

        direct_entitlement, _ = self._direct_entitlement(user, resource, now)
        if direct_entitlement is not None:
            return replace(
                base,
                reason=AccessReason.ENTITLEMENT,
                effective_entitlement=direct_entitlement,
                expires_at=direct_entitlement.expires_at,
            )

        current_subscription, _ = self._current_subscription(user, now)
        candidates: list[tuple[Plan, Subscription | None, Entitlement | None]] = []
        if current_subscription and current_subscription.membership.plan:
            candidates.append((current_subscription.membership.plan, current_subscription, None))
        candidates.extend(
            (plan, None, entitlement) for entitlement, plan in self._plan_entitlements(user, now)
        )
        candidates.sort(key=lambda item: item[0].tier, reverse=True)

        required_plan = self._required_plan(resource)
        for plan, subscription, plan_entitlement in candidates:
            if plan.tier <= Plan.Level.FREE:
                continue
            plan_allowed, _ = self._plan_allows(
                resource=resource,
                plan=plan,
                required_plan=required_plan,
                now=now,
            )
            if not plan_allowed:
                continue
            reason = (
                AccessReason.ENTITLEMENT
                if plan_entitlement is not None
                else AccessReason.ACTIVE_PLAN
            )
            return replace(
                base,
                reason=reason,
                effective_subscription=subscription,
                effective_entitlement=plan_entitlement,
                expires_at=self._candidate_expiry(subscription, plan_entitlement),
            )
        return base

    @staticmethod
    def _is_authenticated(user) -> bool:
        return bool(user and getattr(user, "is_authenticated", False))

    @staticmethod
    def _is_staff(user) -> bool:
        return bool(
            user and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
        )

    @staticmethod
    def _is_editorially_published(resource, *, now=None) -> bool:
        if getattr(resource, "status", None) != AccessPolicy._PUBLISHED_STATUS:
            return False

        # Episode state cannot publish content whose owning Podcast is still a
        # draft, archived, or scheduled for the future. Non-Episode resources
        # without a Podcast relationship retain the original status-only rule.
        try:
            podcast = resource.podcast
        except AttributeError, TypeError:
            return True
        if getattr(podcast, "status", None) is None:
            return True
        published_at = getattr(podcast, "published_at", None)
        structure = getattr(podcast, "structure", None)
        now = now or timezone.now()
        return bool(
            podcast.status == AccessPolicy._PUBLISHED_STATUS
            and published_at is not None
            and published_at <= now
            and getattr(podcast, "parent_id", None) is None
            and structure in {"PARENT", "STANDALONE"}
        )

    @staticmethod
    def _is_public(resource, now) -> bool:
        release_at = getattr(resource, "public_available_at", None)
        return bool(
            AccessPolicy._is_editorially_published(resource, now=now)
            and release_at is not None
            and release_at <= now
        )

    @staticmethod
    def _release_is_future(resource, now) -> bool:
        if not AccessPolicy._is_editorially_published(resource, now=now):
            return True
        release_times = (
            getattr(resource, "premium_available_at", None),
            getattr(resource, "public_available_at", None),
        )
        return any(release_at is not None and release_at > now for release_at in release_times)

    @staticmethod
    def _preview_available(resource) -> bool:
        if getattr(resource, "preview_duration_seconds", 0):
            return True
        try:
            return resource.audios.filter(quality="preview").exists()
        except AttributeError, TypeError, ValueError:
            return False

    @staticmethod
    def _required_plan(resource) -> Plan | None:
        """Read the canonical explicit episode gate; categories are content tags."""

        if getattr(resource, "required_plan_id", None) is None:
            return None
        try:
            return resource.required_plan
        except AttributeError, Plan.DoesNotExist:
            return None

    @staticmethod
    def _direct_entitlement(user, resource, now):
        try:
            content_type = ContentType.objects.get_for_model(resource)
            entitlement = Entitlement.objects.filter(
                user=user,
                content_type=content_type,
                object_id=str(resource.pk),
            ).first()
        except AttributeError, TypeError, ValueError:
            return None, None

        if entitlement is None:
            return None, None
        if entitlement.revoked:
            return None, AccessReason.REVOKED
        if entitlement.expires_at is not None and entitlement.expires_at <= now:
            return None, AccessReason.EXPIRED
        return entitlement, None

    @staticmethod
    def _current_subscription(user, now):
        subscriptions = list(
            Subscription.objects.filter(membership__user=user)
            .select_related("membership__plan")
            .order_by("-membership__plan__tier", "-start_date")
        )
        for subscription in subscriptions:
            if AccessPolicy._subscription_is_current(subscription, now):
                return subscription, True
        return None, bool(subscriptions)

    @staticmethod
    def _subscription_is_current(subscription, now) -> bool:
        if subscription.start_date and subscription.start_date > now:
            return False
        if subscription.status == Subscription.Status.ACTIVE:
            return subscription.end_date is None or subscription.end_date > now
        if subscription.status == Subscription.Status.TRIAL:
            return bool(subscription.trial_ends and subscription.trial_ends > now)
        if subscription.status == Subscription.Status.CANCELED:
            # Transitional interpretation for cancel-at-period-end rows in the
            # current schema. Immediate cancellation stores end_date <= now.
            return bool(subscription.end_date and subscription.end_date > now)
        return False

    @staticmethod
    def _plan_entitlements(user, now):
        plan_content_type = ContentType.objects.get_for_model(Plan)
        entitlements = list(Entitlement.objects.filter(user=user, content_type=plan_content_type))
        valid = [
            entitlement
            for entitlement in entitlements
            if not entitlement.revoked
            and (entitlement.expires_at is None or entitlement.expires_at > now)
        ]
        if not valid:
            return []

        plans = {
            str(plan.pk): plan
            for plan in Plan.objects.filter(pk__in=[entitlement.object_id for entitlement in valid])
        }
        return [
            (entitlement, plans[entitlement.object_id])
            for entitlement in valid
            if entitlement.object_id in plans
        ]

    @staticmethod
    def _plan_allows(*, resource, plan, required_plan, now):
        if not AccessPolicy._is_editorially_published(resource, now=now):
            return False, AccessReason.NOT_YET_RELEASED

        public_at = getattr(resource, "public_available_at", None)
        if public_at is not None and public_at <= now:
            return True, AccessReason.ACTIVE_PLAN

        visibility = getattr(resource, "visibility", None)
        if visibility == AccessPolicy._ENTITLEMENT_VISIBILITY:
            return False, AccessReason.REQUIRES_PLAN
        if visibility == AccessPolicy._PLAN_VISIBILITY and required_plan is None:
            return False, AccessReason.REQUIRES_PLAN
        if required_plan is not None and plan.tier < required_plan.tier:
            return False, AccessReason.REQUIRES_PLAN

        premium_at = getattr(resource, "premium_available_at", None)
        if premium_at is not None and premium_at <= now:
            if visibility in {
                AccessPolicy._MEMBERS_VISIBILITY,
                AccessPolicy._PLAN_VISIBILITY,
            }:
                return True, AccessReason.ACTIVE_PLAN
            if visibility == AccessPolicy._PUBLIC_VISIBILITY and plan.tier > Plan.Level.FREE:
                return True, AccessReason.ACTIVE_PLAN

        feature = plan.get_feature(Feature.Kind.EARLY_ACCESS)
        if feature is None:
            return False, AccessReason.NOT_YET_RELEASED
        target_at = premium_at or public_at
        if target_at is None:
            return False, AccessReason.NOT_YET_RELEASED
        episode_hours = getattr(resource, "early_access_hours", None)
        early_hours = feature.early_access_hours or 0 if episode_hours is None else episode_hours
        available_at = target_at - datetime.timedelta(hours=early_hours)
        if now >= available_at:
            return True, AccessReason.EARLY_ACCESS
        return False, AccessReason.NOT_YET_RELEASED

    @staticmethod
    def _candidate_expiry(subscription, entitlement):
        if entitlement is not None:
            return entitlement.expires_at
        if subscription is None:
            return None
        if subscription.status == Subscription.Status.TRIAL:
            return subscription.trial_ends
        return subscription.end_date


access_policy = AccessPolicy()
