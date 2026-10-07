"""Typed, validated configuration for the selected Cloudflare media adapters."""

from __future__ import annotations

import base64
import binascii
import ipaddress
from collections.abc import Sequence
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.core.exceptions import ImproperlyConfigured


def _required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ImproperlyConfigured(f"{name} is required for Cloudflare media")
    return value.strip()


def _positive(
    name: str,
    value: object,
    *,
    minimum: int = 1,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ImproperlyConfigured(f"{name} must be a positive integer")
    if value < minimum:
        raise ImproperlyConfigured(f"{name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ImproperlyConfigured(f"{name} must be at most {maximum}")
    return value


def _https_origin(name: str, value: object, *, reject_r2_dev: bool = False) -> str:
    candidate = _required_text(name, value).rstrip("/")
    try:
        parsed = urlsplit(candidate)
        port = parsed.port
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} must be a valid HTTPS origin") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ImproperlyConfigured(
            f"{name} must be an absolute HTTPS origin without credentials or a path"
        )
    if port is not None and not 1 <= port <= 65535:  # pragma: no cover
        raise ImproperlyConfigured(f"{name} contains an invalid port")
    try:
        ipaddress.ip_address(parsed.hostname)
    except ValueError:
        pass
    else:
        raise ImproperlyConfigured(f"{name} must use a DNS hostname")
    hostname = parsed.hostname.lower().rstrip(".")
    if reject_r2_dev and (hostname == "r2.dev" or hostname.endswith(".r2.dev")):
        raise ImproperlyConfigured(f"{name} must use a production R2 custom domain, not r2.dev")
    return candidate


def _stream_allowed_origin(value: object) -> str:
    """Validate a Cloudflare Stream playback hostname, not a browser origin URL."""

    candidate = _required_text("CLOUDFLARE_STREAM_ALLOWED_ORIGINS entry", value)
    wildcard = candidate.startswith("*.")
    hostname = candidate[2:] if wildcard else candidate
    if candidate == "*" or any(character in hostname for character in "/:@?#"):
        raise ImproperlyConfigured(
            "CLOUDFLARE_STREAM_ALLOWED_ORIGINS entries must be DNS hostnames "
            "without a scheme, path, credentials, or port"
        )
    try:
        parsed = urlsplit(f"https://{hostname}")
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise ImproperlyConfigured(
            "CLOUDFLARE_STREAM_ALLOWED_ORIGINS entries must use DNS hostnames"
        )
    if parsed.hostname != hostname.lower().rstrip(".") or "." not in hostname:
        raise ImproperlyConfigured(
            "CLOUDFLARE_STREAM_ALLOWED_ORIGINS entries must be valid DNS hostnames"
        )
    return f"*.{parsed.hostname}" if wildcard else parsed.hostname


@dataclass(frozen=True, slots=True)
class CloudflareMediaConfig:
    account_id: str
    api_token: str = field(repr=False)
    r2_access_key_id: str = field(repr=False)
    r2_secret_access_key: str = field(repr=False)
    r2_private_bucket_name: str
    r2_public_bucket_name: str
    r2_public_base_url: str
    images_account_hash: str
    images_signing_key: str = field(repr=False)
    stream_customer_code: str
    stream_signing_key_id: str
    stream_signing_private_key_b64: str = field(repr=False)
    stream_webhook_secret: str = field(repr=False)
    upload_url_ttl_seconds: int = 600
    private_url_ttl_seconds: int = 600
    upload_max_bytes: int = 5 * 1024 * 1024 * 1024
    upload_max_duration_seconds: int = 36_000
    allowed_upload_origins: Sequence[str] = ()
    stream_allowed_origins: Sequence[str] = ()

    def __post_init__(self) -> None:
        for name in (
            "account_id",
            "api_token",
            "r2_access_key_id",
            "r2_secret_access_key",
            "r2_private_bucket_name",
            "r2_public_bucket_name",
            "images_account_hash",
            "images_signing_key",
            "stream_customer_code",
            "stream_signing_key_id",
            "stream_signing_private_key_b64",
            "stream_webhook_secret",
        ):
            _required_text(name, getattr(self, name))
        if self.r2_private_bucket_name == self.r2_public_bucket_name:
            raise ImproperlyConfigured(
                "R2_PRIVATE_BUCKET_NAME and R2_PUBLIC_BUCKET_NAME must be different"
            )
        try:
            decoded_stream_key = base64.b64decode(
                self.stream_signing_private_key_b64,
                validate=True,
            )
        except (binascii.Error, ValueError) as exc:
            raise ImproperlyConfigured(
                "CLOUDFLARE_STREAM_SIGNING_PRIVATE_KEY_B64 must be valid Base64"
            ) from exc
        if not decoded_stream_key:
            raise ImproperlyConfigured(
                "CLOUDFLARE_STREAM_SIGNING_PRIVATE_KEY_B64 must not decode to empty bytes"
            )
        try:
            stream_private_key = load_pem_private_key(
                decoded_stream_key,
                password=None,
            )
        except (TypeError, ValueError, UnsupportedAlgorithm) as exc:
            raise ImproperlyConfigured(
                "CLOUDFLARE_STREAM_SIGNING_PRIVATE_KEY_B64 must contain an "
                "unencrypted PEM private key"
            ) from exc
        if not isinstance(stream_private_key, rsa.RSAPrivateKey):
            raise ImproperlyConfigured(
                "CLOUDFLARE_STREAM_SIGNING_PRIVATE_KEY_B64 must contain an RSA private key"
            )
        if stream_private_key.key_size < 2048:
            raise ImproperlyConfigured(
                "CLOUDFLARE_STREAM_SIGNING_PRIVATE_KEY_B64 RSA key must be at least 2048 bits"
            )
        _https_origin(
            "R2_PUBLIC_BASE_URL",
            self.r2_public_base_url,
            reject_r2_dev=True,
        )
        _positive(
            "MEDIA_UPLOAD_URL_TTL_SECONDS",
            self.upload_url_ttl_seconds,
            minimum=120,
            maximum=21_600,
        )
        _positive(
            "MEDIA_PRIVATE_URL_TTL_SECONDS",
            self.private_url_ttl_seconds,
            maximum=86_400,
        )
        _positive("MEDIA_UPLOAD_MAX_BYTES", self.upload_max_bytes)
        _positive(
            "MEDIA_UPLOAD_MAX_DURATION_SECONDS",
            self.upload_max_duration_seconds,
            maximum=36_000,
        )
        for origin in self.allowed_upload_origins:
            _https_origin("MEDIA_UPLOAD_ALLOWED_ORIGINS entry", origin)
        if not self.stream_allowed_origins:
            raise ImproperlyConfigured(
                "CLOUDFLARE_STREAM_ALLOWED_ORIGINS must contain at least one hostname"
            )
        for origin in self.stream_allowed_origins:
            _stream_allowed_origin(origin)

    @classmethod
    def from_django_settings(cls, settings) -> CloudflareMediaConfig:
        return cls(
            account_id=settings.CLOUDFLARE_ACCOUNT_ID,
            api_token=settings.CLOUDFLARE_API_TOKEN,
            r2_access_key_id=settings.R2_ACCESS_KEY_ID,
            r2_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            r2_private_bucket_name=settings.R2_PRIVATE_BUCKET_NAME,
            r2_public_bucket_name=settings.R2_PUBLIC_BUCKET_NAME,
            r2_public_base_url=settings.R2_PUBLIC_BASE_URL,
            images_account_hash=settings.CLOUDFLARE_IMAGES_ACCOUNT_HASH,
            images_signing_key=settings.CLOUDFLARE_IMAGES_SIGNING_KEY,
            stream_customer_code=settings.CLOUDFLARE_STREAM_CUSTOMER_CODE,
            stream_signing_key_id=settings.CLOUDFLARE_STREAM_SIGNING_KEY_ID,
            stream_signing_private_key_b64=settings.CLOUDFLARE_STREAM_SIGNING_PRIVATE_KEY_B64,
            stream_webhook_secret=settings.CLOUDFLARE_STREAM_WEBHOOK_SECRET,
            upload_url_ttl_seconds=settings.MEDIA_UPLOAD_URL_TTL_SECONDS,
            private_url_ttl_seconds=settings.MEDIA_PRIVATE_URL_TTL_SECONDS,
            upload_max_bytes=settings.MEDIA_UPLOAD_MAX_BYTES,
            upload_max_duration_seconds=settings.MEDIA_UPLOAD_MAX_DURATION_SECONDS,
            allowed_upload_origins=settings.MEDIA_UPLOAD_ALLOWED_ORIGINS,
            stream_allowed_origins=settings.CLOUDFLARE_STREAM_ALLOWED_ORIGINS,
        )
