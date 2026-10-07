"""Server-side validation and idempotent completion for direct R2 uploads."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import PurePath
from typing import Protocol
from uuid import UUID, uuid4

from django.db import transaction

from .canonical import MediaAsset, MediaLocation
from .providers.contracts import MediaProviderError, ObjectMetadata, ObjectStorage

logger = logging.getLogger(__name__)


class UploadFinalizationRejected(ValueError):
    """Raised when a direct upload cannot become a canonical available object."""


class FinalizationActor(Protocol):
    pk: object
    is_authenticated: bool


@dataclass(frozen=True, slots=True)
class R2FinalizationRequest:
    asset_id: UUID
    key: str


@dataclass(frozen=True, slots=True)
class UploadDeclaration:
    media_type: str
    mime_type: str
    byte_size: int | None
    checksum_algorithm: str
    checksum: str
    original_filename: str

    @classmethod
    def from_asset(cls, asset: MediaAsset) -> UploadDeclaration:
        return cls(
            media_type=asset.media_type,
            mime_type=asset.mime_type,
            byte_size=asset.byte_size,
            checksum_algorithm=asset.checksum_algorithm,
            checksum=asset.checksum,
            original_filename=asset.original_filename,
        )


class R2UploadFinalizer:
    """Validate and promote a temporary R2 upload to a private immutable source."""

    FINALIZABLE_STATUSES = {
        MediaAsset.Status.PENDING_UPLOAD,
        MediaAsset.Status.FAILED,
    }

    def __init__(
        self,
        *,
        private_object_storage: ObjectStorage,
        private_container: str,
        max_upload_bytes: int,
    ) -> None:
        self.private_object_storage = private_object_storage
        self.private_container = private_container
        self.max_upload_bytes = max_upload_bytes

    def finalize(
        self,
        request: R2FinalizationRequest,
        *,
        actor: FinalizationActor,
    ) -> MediaLocation:
        asset = MediaAsset.objects.filter(pk=request.asset_id).first()
        if asset is None:
            raise UploadFinalizationRejected("Media asset is not available for finalization")
        self._validate_identity(asset, request, actor)
        declaration = UploadDeclaration.from_asset(asset)
        storage = self.private_object_storage
        existing = self._existing_location(asset, self.private_container)
        if existing is not None:
            self._cleanup_temporary(storage, request.key, asset.pk)
            return existing
        if asset.status not in self.FINALIZABLE_STATUSES:
            raise UploadFinalizationRejected("Media asset is not accepting upload finalization")

        remote = storage.head(key=request.key)
        if remote is None:
            raise UploadFinalizationRejected("Uploaded object was not found")
        if remote.resource_id != request.key:
            raise UploadFinalizationRejected(
                "Provider object identity does not match the upload key"
            )

        rejection = self._validation_error(asset, remote)
        if rejection is not None:
            try:
                storage.delete(key=request.key)
            finally:
                MediaAsset.objects.filter(
                    pk=asset.pk,
                    status__in=self.FINALIZABLE_STATUSES,
                ).update(status=MediaAsset.Status.FAILED)
            raise UploadFinalizationRejected(rejection)

        destination_key = self._destination_key(asset, request.key, remote.etag)
        reservation, promotion_attempt_id = self._reserve_destination(
            asset=asset,
            request=request,
            actor=actor,
            declaration=declaration,
            destination_key=destination_key,
            remote=remote,
        )
        if promotion_attempt_id is None:
            self._cleanup_temporary(storage, request.key, asset.pk)
            return reservation

        promoted = storage.promote(
            source_container=self.private_container,
            source_key=request.key,
            destination_key=destination_key,
            source_etag=remote.etag or "",
            content_type=asset.mime_type,
        )
        promoted_rejection = self._validation_error(asset, promoted)
        if promoted.resource_id != destination_key or promoted_rejection is not None:
            self._mark_reservation_failed(
                reservation,
                promotion_attempt_id=promotion_attempt_id,
                reason=promoted_rejection or "promoted_identity_mismatch",
                fail_asset=True,
            )
            self._cleanup_temporary(storage, request.key, asset.pk)
            raise UploadFinalizationRejected(
                promoted_rejection or "Promoted object identity does not match"
            )

        location = self._activate_destination(
            reservation=reservation,
            request=request,
            actor=actor,
            declaration=declaration,
            promoted=promoted,
            source_etag=remote.etag or "",
            promotion_attempt_id=promotion_attempt_id,
        )
        self._cleanup_temporary(storage, request.key, asset.pk)
        return location

    @staticmethod
    def _cleanup_temporary(storage: ObjectStorage, key: str, asset_id: UUID) -> None:
        try:
            storage.delete(key=key)
        except MediaProviderError as exc:
            logger.warning(
                "Temporary R2 cleanup failed for media asset %s (%s)",
                asset_id,
                exc.operation,
            )

    @transaction.atomic
    def _reserve_destination(
        self,
        *,
        asset: MediaAsset,
        request: R2FinalizationRequest,
        actor: FinalizationActor,
        declaration: UploadDeclaration,
        destination_key: str,
        remote: ObjectMetadata,
    ) -> tuple[MediaLocation, str | None]:
        locked_asset = MediaAsset.objects.select_for_update().get(pk=asset.pk)
        self._validate_identity(locked_asset, request, actor)
        if UploadDeclaration.from_asset(locked_asset) != declaration:
            raise UploadFinalizationRejected("Media upload declaration changed before promotion")
        existing = self._existing_location(
            locked_asset,
            self.private_container,
            for_update=True,
        )
        if existing is not None:
            return existing, None
        if locked_asset.status not in self.FINALIZABLE_STATUSES:
            raise UploadFinalizationRejected("Media asset is not accepting upload finalization")

        reservation = (
            MediaLocation.objects.select_for_update()
            .filter(
                provider=MediaLocation.Provider.CLOUDFLARE,
                product=MediaLocation.Product.R2,
                container=self.private_container,
                locator=destination_key,
            )
            .first()
        )
        if reservation is not None:
            if reservation.asset_id != locked_asset.pk:
                raise UploadFinalizationRejected(
                    "Uploaded object is already assigned to another asset"
                )
            if reservation.status == MediaLocation.Status.AVAILABLE:
                return reservation, None
            if reservation.status == MediaLocation.Status.PENDING:
                raise UploadFinalizationRejected("Upload finalization is already in progress")
            raise UploadFinalizationRejected(
                "A failed upload promotion requires a fresh upload capability"
            )

        promotion_attempt_id = uuid4().hex
        reservation = MediaLocation(
            asset=locked_asset,
            provider=MediaLocation.Provider.CLOUDFLARE,
            product=MediaLocation.Product.R2,
            container=self.private_container,
            locator=destination_key,
        )
        reservation.status = MediaLocation.Status.PENDING
        reservation.is_primary = False
        reservation.etag = ""
        reservation.metadata = {
            "byte_size": remote.byte_size,
            "content_type": remote.content_type or "",
            "source_etag": remote.etag or "",
            "temporary_key": request.key,
            "promotion_state": "promoting",
            "promotion_attempt_id": promotion_attempt_id,
        }
        reservation.save()
        return reservation, promotion_attempt_id

    @transaction.atomic
    def _activate_destination(
        self,
        *,
        reservation: MediaLocation,
        request: R2FinalizationRequest,
        actor: FinalizationActor,
        declaration: UploadDeclaration,
        promoted: ObjectMetadata,
        source_etag: str,
        promotion_attempt_id: str,
    ) -> MediaLocation:
        locked_asset = MediaAsset.objects.select_for_update().get(pk=reservation.asset_id)
        self._validate_identity(locked_asset, request, actor)
        if UploadDeclaration.from_asset(locked_asset) != declaration:
            raise UploadFinalizationRejected("Media upload declaration changed during finalization")
        locked_reservation = MediaLocation.objects.select_for_update().get(pk=reservation.pk)
        if not self._owns_promotion_attempt(
            locked_reservation,
            request=request,
            promotion_attempt_id=promotion_attempt_id,
        ):
            raise UploadFinalizationRejected("Upload promotion attempt is no longer active")
        existing = self._existing_location(
            locked_asset,
            self.private_container,
            for_update=True,
        )
        if existing is not None:
            if existing.pk != locked_reservation.pk:
                locked_reservation.status = MediaLocation.Status.FAILED
                locked_reservation.metadata = {
                    **locked_reservation.metadata,
                    "promotion_state": "superseded",
                }
                locked_reservation.save(update_fields=("status", "metadata", "updated_at"))
            return existing
        if locked_asset.status not in self.FINALIZABLE_STATUSES:
            raise UploadFinalizationRejected("Media asset is not accepting upload finalization")

        is_first_location = not MediaLocation.objects.filter(
            asset=locked_asset,
            is_primary=True,
        ).exists()
        locked_reservation.status = MediaLocation.Status.AVAILABLE
        locked_reservation.is_primary = locked_reservation.is_primary or is_first_location
        locked_reservation.etag = promoted.etag or ""
        locked_reservation.metadata = {
            "content_type": promoted.content_type or "",
            "byte_size": promoted.byte_size,
            "source_etag": source_etag,
            "immutable_promotion": True,
        }
        locked_reservation.save()
        locked_asset.status = MediaAsset.Status.UPLOADED
        locked_asset.save(update_fields=("status", "updated_at"))
        return locked_reservation

    @transaction.atomic
    def _mark_reservation_failed(
        self,
        reservation: MediaLocation,
        *,
        promotion_attempt_id: str,
        reason: str,
        fail_asset: bool,
    ) -> None:
        locked = MediaLocation.objects.select_for_update().get(pk=reservation.pk)
        if not self._owns_promotion_attempt(
            locked,
            request=None,
            promotion_attempt_id=promotion_attempt_id,
        ):
            return
        locked.status = MediaLocation.Status.FAILED
        locked.metadata = {
            **locked.metadata,
            "promotion_state": "failed",
            "failure_reason": reason,
        }
        locked.save(update_fields=("status", "metadata", "updated_at"))
        if fail_asset:
            MediaAsset.objects.filter(
                pk=reservation.asset_id,
                status__in=self.FINALIZABLE_STATUSES,
            ).update(status=MediaAsset.Status.FAILED)

    @staticmethod
    def _owns_promotion_attempt(
        reservation: MediaLocation,
        *,
        request: R2FinalizationRequest | None,
        promotion_attempt_id: str,
    ) -> bool:
        metadata = reservation.metadata
        return (
            reservation.status == MediaLocation.Status.PENDING
            and metadata.get("promotion_state") == "promoting"
            and metadata.get("promotion_attempt_id") == promotion_attempt_id
            and (request is None or metadata.get("temporary_key") == request.key)
        )

    def _existing_location(
        self,
        asset: MediaAsset,
        container: str,
        *,
        for_update: bool = False,
    ) -> MediaLocation | None:
        queryset = MediaLocation.objects.filter(
            asset=asset,
            provider=MediaLocation.Provider.CLOUDFLARE,
            product=MediaLocation.Product.R2,
            container=container,
            locator__startswith=f"canonical/{asset.media_type}/{asset.pk.hex}/",
            status=MediaLocation.Status.AVAILABLE,
        ).order_by("-is_primary", "created_at")
        if for_update:
            queryset = queryset.select_for_update()
        return queryset.first()

    @staticmethod
    def _validate_identity(
        asset: MediaAsset,
        request: R2FinalizationRequest,
        actor: FinalizationActor,
    ) -> None:
        actor_id = actor.pk if actor.is_authenticated else None
        if asset.created_by_id is None or actor_id != asset.created_by_id:
            raise UploadFinalizationRejected("Media asset is not available for finalization")
        if asset.status == MediaAsset.Status.DELETED:
            raise UploadFinalizationRejected("Deleted media cannot be finalized")
        expected_stem = f"temporary/uploads/{asset.pk.hex}/"
        suffix = request.key.removeprefix(expected_stem)
        if (
            not request.key.startswith(expected_stem)
            or not suffix
            or "/" in suffix
            or len(suffix) > 80
        ):
            raise UploadFinalizationRejected("Upload key does not belong to this asset")

    @staticmethod
    def _destination_key(
        asset: MediaAsset,
        source_key: str,
        source_etag: str | None,
    ) -> str:
        if not source_etag:
            raise UploadFinalizationRejected("Uploaded object is missing an integrity ETag")
        suffix = PurePath(source_key).suffix.lower()[:16]
        digest = hashlib.sha256(
            b"\0".join(
                (
                    str(asset.pk).encode(),
                    source_key.encode(),
                    source_etag.encode(),
                )
            )
        ).hexdigest()
        return f"canonical/{asset.media_type}/{asset.pk.hex}/{digest}{suffix}"

    def _validation_error(
        self,
        asset: MediaAsset,
        remote: ObjectMetadata,
    ) -> str | None:
        if asset.byte_size is None or asset.byte_size <= 0:
            return "Media asset is missing its declared upload size"
        if not remote.etag:
            return "Uploaded object is missing an integrity ETag"
        if remote.byte_size != asset.byte_size:
            return "Uploaded object size does not match the declared size"
        if remote.byte_size > self.max_upload_bytes:
            return "Uploaded object exceeds the configured size limit"
        if not asset.mime_type or remote.content_type != asset.mime_type:
            return "Uploaded object content type does not match the declared type"
        if asset.checksum and asset.checksum_algorithm.lower() != "sha256":
            return "Media asset uses an unsupported checksum algorithm"
        if asset.checksum and not remote.checksum:
            return "Uploaded object has no trusted checksum proof"
        if asset.checksum and remote.checksum and remote.checksum.lower() != asset.checksum.lower():
            return "Uploaded object checksum does not match the declared checksum"
        return None
