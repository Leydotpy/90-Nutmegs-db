"""Access-bound media delivery over provider-neutral adapters."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Protocol

from django.utils import timezone

from .canonical import MediaAccessClass, MediaAsset, MediaLocation, MediaVariant
from .providers.contracts import (
    DeliveryDescriptor,
    ImagePlatform,
    ObjectStorage,
    VideoPlatform,
)


class AccessDecisionLike(Protocol):
    allowed: bool
    action: object
    resource_label: str
    resource_id: str
    principal_id: str
    media_variant_id: str
    media_access_class: str
    expires_at: datetime | None


class DeliveryActor(Protocol):
    pk: object
    is_authenticated: bool


class MediaDeliveryDenied(PermissionError):
    """Raised before any provider capability is minted for an invalid binding."""


class MediaDeliveryService:
    """Mint one bounded capability for the exact authorized episode variant."""

    DOWNLOAD_ACTION = "download"

    def __init__(
        self,
        *,
        private_object_storage: ObjectStorage,
        public_object_storage: ObjectStorage,
        image_platform: ImagePlatform,
        video_platform: VideoPlatform,
        private_container: str,
        public_container: str,
        private_ttl_seconds: int,
    ) -> None:
        if private_ttl_seconds <= 0 or private_ttl_seconds > 86_400:
            raise ValueError("Private media TTL must be between 1 and 86400 seconds")
        self.private_object_storage = private_object_storage
        self.public_object_storage = public_object_storage
        self.image_platform = image_platform
        self.video_platform = video_platform
        self.private_container = private_container
        self.public_container = public_container
        self.private_ttl_seconds = private_ttl_seconds

    @staticmethod
    def _require_binding(
        *,
        decision: AccessDecisionLike,
        actor: DeliveryActor,
        variant: MediaVariant,
        location: MediaLocation,
        action: str,
        product: str,
        allowed_actions: frozenset[str],
        now: datetime,
    ) -> None:
        if not decision.allowed:
            raise MediaDeliveryDenied("Media delivery is not authorized")
        actor_id = str(actor.pk) if actor and actor.is_authenticated else ""
        if decision.principal_id != actor_id:
            raise MediaDeliveryDenied("Access decision is not bound to this principal")
        decision_action = getattr(decision.action, "value", decision.action)
        requested_action = getattr(action, "value", action)
        if decision_action != requested_action:
            raise MediaDeliveryDenied("Access decision action does not match delivery")
        if requested_action not in allowed_actions:
            raise MediaDeliveryDenied("Access decision action cannot mint this media capability")
        if decision.expires_at is not None and decision.expires_at <= now:
            raise MediaDeliveryDenied("Access decision has expired")
        if (
            variant.episode_id is None
            or decision.resource_label != "podcasts.episode"
            or decision.resource_id != str(variant.episode_id)
        ):
            raise MediaDeliveryDenied("Access decision is not bound to this episode")
        if variant.status != MediaVariant.Status.READY:
            raise MediaDeliveryDenied("Media variant is not ready")
        if variant.asset.status != MediaAsset.Status.READY:
            raise MediaDeliveryDenied("Media asset is not ready")
        if (
            decision.media_variant_id != str(variant.pk)
            or decision.media_access_class != variant.effective_access_class
        ):
            raise MediaDeliveryDenied("Access decision is not bound to this media variant")
        if (
            location.asset_id != variant.asset_id
            or location.provider != MediaLocation.Provider.CLOUDFLARE
            or location.status != MediaLocation.Status.AVAILABLE
            or location.product != product
        ):
            raise MediaDeliveryDenied("Media location is not valid for this variant")

    @staticmethod
    def _is_public(variant: MediaVariant) -> bool:
        return variant.effective_access_class == MediaAccessClass.PUBLIC

    def _bounded_ttl(self, decision: AccessDecisionLike, now: datetime) -> int:
        ttl = self.private_ttl_seconds
        if decision.expires_at is not None:
            ttl = min(ttl, int((decision.expires_at - now).total_seconds()))
        if ttl < 1:
            raise MediaDeliveryDenied("Access decision expires too soon")
        return ttl

    def _require_object_visibility(
        self,
        *,
        variant: MediaVariant,
        location: MediaLocation,
    ) -> None:
        expected = self.public_container if self._is_public(variant) else self.private_container
        if location.container != expected:
            raise MediaDeliveryDenied("R2 location visibility does not match media access")

    @staticmethod
    def _require_managed_visibility(
        *,
        variant: MediaVariant,
        location: MediaLocation,
    ) -> None:
        requires_signed_delivery = location.metadata.get("requires_signed_delivery")
        expected = not MediaDeliveryService._is_public(variant)
        if requires_signed_delivery is not expected:
            raise MediaDeliveryDenied("Provider visibility does not match media access")

    def deliver_object(
        self,
        *,
        decision: AccessDecisionLike,
        actor: DeliveryActor,
        variant: MediaVariant,
        location: MediaLocation,
        action: str,
        response_content_disposition: str | None = None,
        now: datetime | None = None,
    ) -> DeliveryDescriptor:
        issued_at = now or timezone.now()
        self._require_binding(
            decision=decision,
            actor=actor,
            variant=variant,
            location=location,
            action=action,
            product=MediaLocation.Product.R2,
            allowed_actions=frozenset({"stream", "download"}),
            now=issued_at,
        )
        self._require_object_visibility(variant=variant, location=location)
        if self._is_public(variant):
            return self.public_object_storage.build_public_url(key=location.locator)
        ttl = self._bounded_ttl(decision, issued_at)
        return self.private_object_storage.create_download_capability(
            key=location.locator,
            expires_in=ttl,
            response_content_disposition=response_content_disposition,
        )

    def deliver_image(
        self,
        *,
        decision: AccessDecisionLike,
        actor: DeliveryActor,
        variant: MediaVariant,
        location: MediaLocation,
        image_variant: str,
        action: str,
        now: datetime | None = None,
    ) -> DeliveryDescriptor:
        issued_at = now or timezone.now()
        self._require_binding(
            decision=decision,
            actor=actor,
            variant=variant,
            location=location,
            action=action,
            product=MediaLocation.Product.IMAGES,
            allowed_actions=frozenset({"stream"}),
            now=issued_at,
        )
        self._require_managed_visibility(variant=variant, location=location)
        if self._is_public(variant):
            return self.image_platform.build_public_variant(
                image_id=location.locator,
                variant=image_variant,
            )
        return self.image_platform.sign_private_variant(
            image_id=location.locator,
            variant=image_variant,
            expires_at=issued_at + timedelta(seconds=self._bounded_ttl(decision, issued_at)),
        )

    def deliver_video(
        self,
        *,
        decision: AccessDecisionLike,
        actor: DeliveryActor,
        variant: MediaVariant,
        location: MediaLocation,
        action: str,
        downloadable: bool = False,
        now: datetime | None = None,
    ) -> DeliveryDescriptor:
        issued_at = now or timezone.now()
        self._require_binding(
            decision=decision,
            actor=actor,
            variant=variant,
            location=location,
            action=action,
            product=MediaLocation.Product.STREAM,
            allowed_actions=frozenset({"stream", "download"}),
            now=issued_at,
        )
        self._require_managed_visibility(variant=variant, location=location)
        requested_action = getattr(action, "value", action)
        if downloadable and requested_action != self.DOWNLOAD_ACTION:
            raise MediaDeliveryDenied("Downloadable playback requires a download access decision")
        private = not self._is_public(variant)
        ttl = self._bounded_ttl(decision, issued_at) if private else None
        return self.video_platform.get_playback_descriptor(
            video_id=location.locator,
            private=private,
            expires_at=issued_at + timedelta(seconds=ttl) if ttl is not None else None,
            downloadable=downloadable,
        )
