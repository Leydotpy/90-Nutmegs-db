"""Stable media-provider contracts owned by SANFootball.

Bearer upload/download URLs are deliberately excluded from representations.  These
value objects may be returned to an authorized client, but must never be logged,
stored in models, or used as canonical media identity.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable


class MediaProviderError(RuntimeError):
    """Safe infrastructure error that does not embed credentials or capability URLs."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        operation: str,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.operation = operation
        self.retryable = retryable


@dataclass(frozen=True, slots=True)
class UploadIntent:
    provider: str
    product: str
    resource_id: str
    upload_url: str = field(repr=False)
    method: str = "POST"
    headers: Mapping[str, str] = field(default_factory=dict, repr=False)
    expires_at: datetime | None = None
    resumable: bool = False


@dataclass(frozen=True, slots=True)
class ObjectMetadata:
    resource_id: str
    byte_size: int
    etag: str | None = None
    content_type: str | None = None
    checksum: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict, repr=False)


@dataclass(frozen=True, slots=True)
class ProviderStatus:
    resource_id: str
    state: str
    ready: bool
    details: Mapping[str, object] = field(default_factory=dict, repr=False)


@dataclass(frozen=True, slots=True)
class DeliveryDescriptor:
    provider: str
    product: str
    resource_id: str
    urls: Mapping[str, str] = field(repr=False)
    expires_at: datetime | None = None
    protected: bool = True


@runtime_checkable
class ObjectStorage(Protocol):
    def create_upload_intent(
        self,
        *,
        key: str,
        content_type: str,
        expires_in: int,
    ) -> UploadIntent: ...

    def head(self, *, key: str) -> ObjectMetadata | None: ...

    def promote(
        self,
        *,
        source_container: str,
        source_key: str,
        destination_key: str,
        source_etag: str,
        content_type: str,
    ) -> ObjectMetadata: ...

    def create_download_capability(
        self,
        *,
        key: str,
        expires_in: int,
        response_content_disposition: str | None = None,
    ) -> DeliveryDescriptor: ...

    def build_public_url(self, *, key: str) -> DeliveryDescriptor: ...

    def delete(self, *, key: str) -> None: ...


@runtime_checkable
class ImagePlatform(Protocol):
    def create_upload_intent(
        self,
        *,
        creator_id: str,
        metadata: Mapping[str, object],
        private: bool,
        expires_at: datetime,
    ) -> UploadIntent: ...

    def get_status(self, *, image_id: str) -> ProviderStatus: ...

    def build_public_variant(
        self,
        *,
        image_id: str,
        variant: str,
    ) -> DeliveryDescriptor: ...

    def sign_private_variant(
        self,
        *,
        image_id: str,
        variant: str,
        expires_at: datetime,
    ) -> DeliveryDescriptor: ...

    def delete(self, *, image_id: str) -> None: ...


@runtime_checkable
class VideoPlatform(Protocol):
    def create_upload_intent(
        self,
        *,
        creator_id: str,
        upload_length: int,
        max_duration_seconds: int,
        metadata: Mapping[str, str],
        private: bool,
        allowed_origins: Sequence[str],
        expires_at: datetime,
        prefer_resumable: bool = False,
    ) -> UploadIntent: ...

    def get_status(self, *, video_id: str) -> ProviderStatus: ...

    def get_playback_descriptor(
        self,
        *,
        video_id: str,
        private: bool,
        expires_at: datetime | None = None,
        downloadable: bool = False,
    ) -> DeliveryDescriptor: ...

    def verify_webhook(self, *, raw_body: bytes, signature_header: str) -> bool: ...

    def delete(self, *, video_id: str) -> None: ...
