"""Direct-upload orchestration over provider-neutral media contracts."""

from __future__ import annotations

import mimetypes
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import PurePath
from typing import Protocol
from uuid import UUID, uuid4

from django.db import transaction
from django.utils import timezone

from .canonical import MediaAsset
from .providers.contracts import ImagePlatform, ObjectStorage, UploadIntent, VideoPlatform


class UploadIntentRejected(ValueError):
    """Raised before any provider call when requested upload policy is invalid."""


class UploadActor(Protocol):
    pk: object
    is_authenticated: bool


@dataclass(frozen=True, slots=True)
class UploadIntentRequest:
    asset_id: UUID
    product: str
    max_duration_seconds: int | None = None
    prefer_resumable: bool = False


class UploadIntentService:
    """Issue a narrowly scoped capability for one owned pending media asset.

    Identity, size, MIME type, filename, and access class come from the canonical
    database row rather than request data. The service never receives or proxies the
    file body.
    """

    def __init__(
        self,
        *,
        private_object_storage: ObjectStorage,
        image_platform: ImagePlatform,
        video_platform: VideoPlatform,
        max_upload_bytes: int,
        max_duration_seconds: int,
        upload_ttl_seconds: int,
        stream_allowed_origins: Sequence[str] = (),
    ) -> None:
        self.private_object_storage = private_object_storage
        self.image_platform = image_platform
        self.video_platform = video_platform
        self.max_upload_bytes = max_upload_bytes
        self.max_duration_seconds = max_duration_seconds
        self.upload_ttl_seconds = upload_ttl_seconds
        self.stream_allowed_origins = tuple(stream_allowed_origins)

    def create(
        self,
        request: UploadIntentRequest,
        *,
        actor: UploadActor,
        now: datetime | None = None,
    ) -> UploadIntent:
        now = now or timezone.now()
        asset = self._owned_pending_asset(request, actor)
        self._validate(request, asset)
        creator_id = str(actor.pk)
        expires_at = now + timedelta(seconds=self.upload_ttl_seconds)
        metadata = {"sanfootball_asset_id": str(asset.pk)}

        if request.product == "r2":
            extension = self._safe_extension(asset.original_filename, asset.mime_type)
            key = f"temporary/uploads/{asset.pk.hex}/{uuid4().hex}{extension}"
            # Provider-reported metadata is not trusted until completion. Even an
            # eventually public asset must therefore begin in the private bucket.
            return self.private_object_storage.create_upload_intent(
                key=key,
                content_type=asset.mime_type,
                expires_in=self.upload_ttl_seconds,
            )
        if request.product == "images":
            return self.image_platform.create_upload_intent(
                creator_id=creator_id,
                metadata=metadata,
                private=True,
                expires_at=expires_at,
            )
        if request.product == "stream":
            duration = (
                request.max_duration_seconds
                if request.max_duration_seconds is not None
                else self.max_duration_seconds
            )
            return self.video_platform.create_upload_intent(
                creator_id=creator_id,
                upload_length=asset.byte_size,
                max_duration_seconds=duration,
                metadata=metadata,
                private=True,
                allowed_origins=self.stream_allowed_origins,
                expires_at=expires_at,
                prefer_resumable=request.prefer_resumable,
            )
        raise UploadIntentRejected(f"Unsupported media product: {request.product}")

    def _owned_pending_asset(
        self,
        request: UploadIntentRequest,
        actor: UploadActor,
    ) -> MediaAsset:
        with transaction.atomic():
            asset = MediaAsset.objects.select_for_update().filter(pk=request.asset_id).first()
            actor_id = actor.pk if actor and actor.is_authenticated else None
            if asset is None or asset.created_by_id is None or actor_id != asset.created_by_id:
                raise UploadIntentRejected("Media asset is not available for upload")
            if asset.status == MediaAsset.Status.FAILED:
                asset.status = MediaAsset.Status.PENDING_UPLOAD
                asset.save(update_fields=("status", "updated_at"))
            elif asset.status != MediaAsset.Status.PENDING_UPLOAD:
                raise UploadIntentRejected("Media asset is not pending upload")
        return asset

    def _validate(self, request: UploadIntentRequest, asset: MediaAsset) -> None:
        creator_id = str(asset.created_by_id)
        if request.product == "stream" and len(creator_id) > 64:
            raise UploadIntentRejected("Cloudflare Stream creator identity is too long")
        if asset.byte_size is None or asset.byte_size <= 0:
            raise UploadIntentRejected("Upload length must be positive")
        if asset.byte_size > self.max_upload_bytes:
            raise UploadIntentRejected("Upload exceeds the configured size limit")
        if not asset.mime_type or "/" not in asset.mime_type:
            raise UploadIntentRejected("A valid content type is required")
        if asset.checksum:
            raise UploadIntentRejected(
                "Direct-upload checksums must be assigned by trusted processing"
            )
        if request.product == "images" and (
            asset.media_type != MediaAsset.MediaType.IMAGE
            or not asset.mime_type.startswith("image/")
        ):
            raise UploadIntentRejected("Cloudflare Images requires a canonical image asset")
        if request.product == "stream" and (
            asset.media_type != MediaAsset.MediaType.VIDEO
            or not asset.mime_type.startswith("video/")
        ):
            raise UploadIntentRejected("Cloudflare Stream requires a canonical video asset")
        if request.max_duration_seconds is not None:
            requested_duration = request.max_duration_seconds
            if (
                isinstance(requested_duration, bool)
                or not isinstance(requested_duration, int)
                or requested_duration <= 0
            ):
                raise UploadIntentRejected("Video duration must be a positive integer")
            if requested_duration > self.max_duration_seconds:
                raise UploadIntentRejected("Video duration exceeds the configured limit")

    @staticmethod
    def _safe_extension(filename: str, content_type: str) -> str:
        suffix = PurePath(filename).suffix.lower()
        guessed = mimetypes.guess_extension(content_type, strict=False) or ""
        if suffix and guessed and suffix == guessed:
            return suffix[:16]
        return guessed[:16]
