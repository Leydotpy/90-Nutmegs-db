"""Cloudflare R2, Images, and Stream adapters backed exclusively by pycflare."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, NoReturn

from pycflare import CloudflareClient, CloudflareCredentials
from pycflare.exceptions import (
    CloudflareServerError,
    PycflareError,
    RateLimitError,
    TransportError,
)
from pycflare.media import (
    ImagesClient,
    ImagesURLBuilder,
    ImagesURLSigner,
    StreamClient,
    StreamTokenSigner,
    StreamURLBuilder,
    StreamWebhookVerifier,
)
from pycflare.media.stream import BASIC_UPLOAD_MAX_BYTES
from pycflare.storage import R2Client, R2Settings

from .config import CloudflareMediaConfig
from .contracts import (
    DeliveryDescriptor,
    MediaProviderError,
    ObjectMetadata,
    ProviderStatus,
    UploadIntent,
)

PROVIDER = "cloudflare"


def _raise_provider_error(operation: str, exc: PycflareError) -> NoReturn:
    retryable = isinstance(
        exc,
        (CloudflareServerError, RateLimitError, TransportError),
    )
    raise MediaProviderError(
        f"Cloudflare media operation failed: {operation}",
        provider=PROVIDER,
        operation=operation,
        retryable=retryable,
    ) from exc


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


class CloudflareObjectStorage:
    """Provider-neutral object storage implemented by pycflare's R2 client."""

    def __init__(self, client: R2Client) -> None:
        self.client = client

    def create_upload_intent(
        self,
        *,
        key: str,
        content_type: str,
        expires_in: int,
    ) -> UploadIntent:
        try:
            ticket = self.client.presign_put(
                key,
                expires_in=expires_in,
                content_type=content_type,
            )
        except PycflareError as exc:
            _raise_provider_error("r2.presign_put", exc)
        return UploadIntent(
            provider=PROVIDER,
            product="r2",
            resource_id=key,
            upload_url=ticket.url,
            method="PUT",
            headers={"Content-Type": content_type},
            expires_at=ticket.expires_at,
        )

    def head(self, *, key: str) -> ObjectMetadata | None:
        try:
            result = self.client.head(key)
        except PycflareError as exc:
            _raise_provider_error("r2.head", exc)
        if result is None:
            return None
        return ObjectMetadata(
            resource_id=result.key,
            byte_size=result.size,
            etag=result.etag,
            content_type=result.content_type,
            # R2 custom metadata is supplied by the uploader and is not proof of
            # content integrity. A trusted processing step must compute checksums.
            checksum=None,
            metadata=result.metadata,
        )

    def promote(
        self,
        *,
        source_container: str,
        source_key: str,
        destination_key: str,
        source_etag: str,
        content_type: str,
    ) -> ObjectMetadata:
        """Conditionally copy a staged object to this adapter's canonical bucket."""

        if not source_container or not source_etag or not content_type:
            raise MediaProviderError(
                "R2 promotion requires a source container, ETag, and content type",
                provider=PROVIDER,
                operation="r2.copy_object",
            )
        destination_container = self.client.settings.bucket_name
        try:
            self.client.s3.copy_object(
                Bucket=destination_container,
                Key=destination_key,
                CopySource={"Bucket": source_container, "Key": source_key},
                CopySourceIfMatch=source_etag,
                # Do not copy cache, disposition, or custom metadata controlled by
                # the direct uploader into the canonical object.
                MetadataDirective="REPLACE",
                ContentType=content_type,
            )
        except Exception as exc:
            raise MediaProviderError(
                "Cloudflare media operation failed: r2.copy_object",
                provider=PROVIDER,
                operation="r2.copy_object",
                retryable=True,
            ) from exc
        promoted = self.head(key=destination_key)
        if promoted is None:
            raise MediaProviderError(
                "R2 promotion did not create the canonical object",
                provider=PROVIDER,
                operation="r2.copy_object",
                retryable=True,
            )
        return promoted

    def create_download_capability(
        self,
        *,
        key: str,
        expires_in: int,
        response_content_disposition: str | None = None,
    ) -> DeliveryDescriptor:
        if self.client.settings.public_base_url:
            raise MediaProviderError(
                "Protected R2 delivery cannot use a public bucket",
                provider=PROVIDER,
                operation="r2.presign_get",
            )
        try:
            ticket = self.client.presign_get(
                key,
                expires_in=expires_in,
                response_content_disposition=response_content_disposition,
            )
        except PycflareError as exc:
            _raise_provider_error("r2.presign_get", exc)
        return DeliveryDescriptor(
            provider=PROVIDER,
            product="r2",
            resource_id=key,
            urls={"download": ticket.url},
            expires_at=ticket.expires_at,
            protected=True,
        )

    def build_public_url(self, *, key: str) -> DeliveryDescriptor:
        if not self.client.settings.public_base_url:
            raise MediaProviderError(
                "Public R2 delivery requires a configured custom domain",
                provider=PROVIDER,
                operation="r2.public_url",
            )
        try:
            url = self.client.url(key)
        except PycflareError as exc:
            _raise_provider_error("r2.public_url", exc)
        return DeliveryDescriptor(
            provider=PROVIDER,
            product="r2",
            resource_id=key,
            urls={"download": url},
            protected=False,
        )

    def delete(self, *, key: str) -> None:
        try:
            self.client.delete(key)
        except PycflareError as exc:
            _raise_provider_error("r2.delete", exc)


class CloudflareImagePlatform:
    """Cloudflare Images control and delivery behind a SANFootball contract."""

    def __init__(
        self,
        client: ImagesClient,
        *,
        account_hash: str,
        signer: ImagesURLSigner,
    ) -> None:
        self.client = client
        self.account_hash = account_hash
        self.signer = signer

    def create_upload_intent(
        self,
        *,
        creator_id: str,
        metadata: Mapping[str, object],
        private: bool,
        expires_at: datetime,
    ) -> UploadIntent:
        try:
            ticket = self.client.create_direct_upload(
                creator=creator_id,
                expiry=expires_at,
                metadata=metadata,
                require_signed_urls=private,
            )
        except PycflareError as exc:
            _raise_provider_error("images.create_direct_upload", exc)
        return UploadIntent(
            provider=PROVIDER,
            product="images",
            resource_id=ticket.image_id,
            upload_url=ticket.upload_url,
            expires_at=expires_at,
        )

    def get_status(self, *, image_id: str) -> ProviderStatus:
        try:
            payload = _mapping(self.client.get(image_id))
        except PycflareError as exc:
            _raise_provider_error("images.get", exc)
        ready = bool(payload.get("uploaded")) and not bool(payload.get("draft"))
        state = str(payload.get("status") or ("ready" if ready else "pending"))
        return ProviderStatus(
            resource_id=image_id,
            state=state,
            ready=ready,
            details=payload,
        )

    def build_public_variant(
        self,
        *,
        image_id: str,
        variant: str,
    ) -> DeliveryDescriptor:
        url = ImagesURLBuilder.delivery(self.account_hash, image_id, variant)
        return DeliveryDescriptor(
            provider=PROVIDER,
            product="images",
            resource_id=image_id,
            urls={"image": url},
            protected=False,
        )

    def sign_private_variant(
        self,
        *,
        image_id: str,
        variant: str,
        expires_at: datetime,
    ) -> DeliveryDescriptor:
        unsigned = ImagesURLBuilder.delivery(self.account_hash, image_id, variant)
        signed = self.signer.sign(unsigned, expires_at=expires_at)
        return DeliveryDescriptor(
            provider=PROVIDER,
            product="images",
            resource_id=image_id,
            urls={"image": signed},
            expires_at=expires_at,
            protected=True,
        )

    def delete(self, *, image_id: str) -> None:
        try:
            self.client.delete(image_id)
        except PycflareError as exc:
            _raise_provider_error("images.delete", exc)


class CloudflareVideoPlatform:
    """Cloudflare Stream upload, status, secure playback, and webhook adapter."""

    def __init__(
        self,
        client: StreamClient,
        *,
        url_builder: StreamURLBuilder,
        webhook_verifier: StreamWebhookVerifier,
        token_signer: StreamTokenSigner | None = None,
    ) -> None:
        self.client = client
        self.url_builder = url_builder
        self.webhook_verifier = webhook_verifier
        self.token_signer = token_signer

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
    ) -> UploadIntent:
        use_tus = prefer_resumable or upload_length >= BASIC_UPLOAD_MAX_BYTES
        try:
            if use_tus:
                tus_metadata: dict[str, str | bytes | None] = dict(metadata)
                tus_metadata["maxdurationseconds"] = str(max_duration_seconds)
                tus_metadata["expiry"] = (
                    expires_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
                )
                if private:
                    tus_metadata["requiresignedurls"] = None
                tus_ticket = self.client.create_tus_upload(
                    upload_length=upload_length,
                    metadata=tus_metadata,
                    creator=creator_id,
                    direct_user=True,
                )
                if allowed_origins:
                    try:
                        self.client.update(
                            tus_ticket.video_id,
                            allowedOrigins=list(allowed_origins),
                        )
                    except PycflareError as exc:
                        with suppress(PycflareError):
                            self.client.delete(tus_ticket.video_id)
                        _raise_provider_error("stream.set_allowed_origins", exc)
                return UploadIntent(
                    provider=PROVIDER,
                    product="stream",
                    resource_id=tus_ticket.video_id,
                    upload_url=tus_ticket.upload_url,
                    method="PATCH",
                    headers={"Tus-Resumable": "1.0.0"},
                    expires_at=expires_at,
                    resumable=True,
                )

            direct_ticket = self.client.create_direct_upload(
                max_duration_seconds=max_duration_seconds,
                allowed_origins=allowed_origins,
                creator=creator_id,
                expiry=expires_at,
                meta=metadata,
                require_signed_urls=private,
            )
        except PycflareError as exc:
            _raise_provider_error("stream.create_upload", exc)
        return UploadIntent(
            provider=PROVIDER,
            product="stream",
            resource_id=direct_ticket.video_id,
            upload_url=direct_ticket.upload_url,
            expires_at=expires_at,
        )

    def get_status(self, *, video_id: str) -> ProviderStatus:
        try:
            payload = _mapping(self.client.get(video_id))
        except PycflareError as exc:
            _raise_provider_error("stream.get", exc)
        status = _mapping(payload.get("status"))
        ready = bool(payload.get("readyToStream"))
        state = str(status.get("state") or ("ready" if ready else "pending"))
        return ProviderStatus(
            resource_id=video_id,
            state=state,
            ready=ready,
            details=payload,
        )

    def get_playback_descriptor(
        self,
        *,
        video_id: str,
        private: bool,
        expires_at: datetime | None = None,
        downloadable: bool = False,
    ) -> DeliveryDescriptor:
        playback_id = video_id
        if private:
            if expires_at is None:
                raise ValueError("expires_at is required for private Stream playback")
            try:
                if self.token_signer is not None:
                    playback_id = self.token_signer.sign(
                        video_id,
                        expires_at=expires_at,
                        downloadable=downloadable,
                    )
                else:
                    playback_id = self.client.create_playback_token(
                        video_id,
                        exp=int(expires_at.timestamp()),
                        downloadable=downloadable,
                    ).token
            except PycflareError as exc:
                _raise_provider_error("stream.create_playback_token", exc)

        urls = {
            "hls": self.url_builder.hls(playback_id),
            "dash": self.url_builder.dash(playback_id),
            "iframe": self.url_builder.iframe(playback_id),
        }
        if downloadable:
            urls["download"] = self.url_builder.download(playback_id)
        return DeliveryDescriptor(
            provider=PROVIDER,
            product="stream",
            resource_id=video_id,
            urls=urls,
            expires_at=expires_at if private else None,
            protected=private,
        )

    def verify_webhook(self, *, raw_body: bytes, signature_header: str) -> bool:
        return self.webhook_verifier.verify(raw_body, signature_header)

    def delete(self, *, video_id: str) -> None:
        try:
            self.client.delete(video_id)
        except PycflareError as exc:
            _raise_provider_error("stream.delete", exc)


@dataclass(slots=True)
class CloudflareMediaAdapters:
    private_object_storage: CloudflareObjectStorage
    public_object_storage: CloudflareObjectStorage
    images: CloudflareImagePlatform
    video: CloudflareVideoPlatform
    _http_client: CloudflareClient

    def close(self) -> None:
        self.private_object_storage.client.close()
        self.public_object_storage.client.close()
        self._http_client.close()


def build_cloudflare_adapters(config: CloudflareMediaConfig) -> CloudflareMediaAdapters:
    """Build one process-scoped adapter bundle from validated canonical settings."""

    credentials = CloudflareCredentials(
        account_id=config.account_id,
        api_token=config.api_token,
    )
    http_client = CloudflareClient(credentials)
    private_r2_client = R2Client(
        R2Settings(
            account_id=config.account_id,
            access_key_id=config.r2_access_key_id,
            secret_access_key=config.r2_secret_access_key,
            bucket_name=config.r2_private_bucket_name,
            signed_url_expiry=config.private_url_ttl_seconds,
        )
    )
    public_r2_client = R2Client(
        R2Settings(
            account_id=config.account_id,
            access_key_id=config.r2_access_key_id,
            secret_access_key=config.r2_secret_access_key,
            bucket_name=config.r2_public_bucket_name,
            public_base_url=config.r2_public_base_url,
            signed_url_expiry=config.private_url_ttl_seconds,
        )
    )
    try:
        private_key = base64.b64decode(
            config.stream_signing_private_key_b64,
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        http_client.close()
        raise ValueError("CLOUDFLARE_STREAM_SIGNING_PRIVATE_KEY_B64 must be valid Base64") from exc

    return CloudflareMediaAdapters(
        private_object_storage=CloudflareObjectStorage(private_r2_client),
        public_object_storage=CloudflareObjectStorage(public_r2_client),
        images=CloudflareImagePlatform(
            ImagesClient(http_client),
            account_hash=config.images_account_hash,
            signer=ImagesURLSigner(config.images_signing_key),
        ),
        video=CloudflareVideoPlatform(
            StreamClient(http_client),
            url_builder=StreamURLBuilder(customer_code=config.stream_customer_code),
            webhook_verifier=StreamWebhookVerifier(config.stream_webhook_secret),
            token_signer=StreamTokenSigner(
                key_id=config.stream_signing_key_id,
                private_key_pem=private_key,
            ),
        ),
        _http_client=http_client,
    )
