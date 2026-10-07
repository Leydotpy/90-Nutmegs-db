"""Validation helpers for delivering CloudFront-signed HLS cookies."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import quote, urlsplit

from django.utils.dateparse import parse_datetime

CLOUDFRONT_COOKIE_NAMES = frozenset(
    {
        "CloudFront-Key-Pair-Id",
        "CloudFront-Policy",
        "CloudFront-Signature",
    }
)
_DNS_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class HLSDeliveryConfigurationError(ValueError):
    """Raised when an HLS cookie cannot be delivered to both relevant hosts."""


@dataclass(frozen=True)
class HLSCookieScope:
    delivery_host: str
    cookie_domain: str
    request_host: str | None = None


@dataclass(frozen=True)
class HLSResourceScope:
    policy_path: str
    playlist_path: str
    cookie_path: str


def normalize_dns_name(
    value: object,
    *,
    setting_name: str,
    allow_leading_dot: bool = False,
) -> str:
    """Return a canonical DNS name, rejecting URLs, ports, wildcards, and IPs."""

    if not isinstance(value, str):
        raise HLSDeliveryConfigurationError(f"{setting_name} must be a DNS name")

    candidate = value.strip()
    if allow_leading_dot and candidate.startswith("."):
        candidate = candidate[1:]
    candidate = candidate.rstrip(".").lower()
    if not candidate:
        raise HLSDeliveryConfigurationError(f"{setting_name} must be a DNS name")
    if any(token in candidate for token in ("://", "/", "\\", "@", "*", ":")):
        raise HLSDeliveryConfigurationError(
            f"{setting_name} must contain only a DNS name (no scheme, path, port, or wildcard)"
        )

    try:
        candidate = candidate.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise HLSDeliveryConfigurationError(
            f"{setting_name} is not a valid DNS name"
        ) from exc

    if len(candidate) > 253:
        raise HLSDeliveryConfigurationError(f"{setting_name} is too long")
    labels = candidate.split(".")
    if len(labels) < 2 or any(not _DNS_LABEL.fullmatch(label) for label in labels):
        raise HLSDeliveryConfigurationError(
            f"{setting_name} must be a fully qualified DNS name"
        )
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        pass
    else:
        raise HLSDeliveryConfigurationError(f"{setting_name} cannot be an IP address")

    return candidate


def hostname_from_request_host(value: object) -> str:
    """Extract and validate the hostname portion of a Django request host."""

    if not isinstance(value, str) or not value.strip():
        raise HLSDeliveryConfigurationError("The request Host header is unavailable")
    parsed = urlsplit(f"//{value.strip()}")
    if parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise HLSDeliveryConfigurationError("The request Host header is invalid")
    try:
        hostname = parsed.hostname
        # Accessing ``port`` forces urllib to reject malformed/non-numeric ports.
        _request_port = parsed.port
    except ValueError as exc:
        raise HLSDeliveryConfigurationError("The request Host header is invalid") from exc
    return normalize_dns_name(hostname, setting_name="request Host")


def host_is_within_cookie_domain(host: str, cookie_domain: str) -> bool:
    return host == cookie_domain or host.endswith(f".{cookie_domain}")


def resolve_hls_cookie_scope(
    *,
    delivery_host: object,
    cookie_domain: object,
    request_host: object | None = None,
) -> HLSCookieScope:
    """Validate the CDN and, when supplied, API host against one cookie domain."""

    normalized_delivery = normalize_dns_name(
        delivery_host,
        setting_name="CLOUDFRONT_DOMAIN",
    )
    normalized_cookie = normalize_dns_name(
        cookie_domain,
        setting_name="CLOUDFRONT_COOKIE_DOMAIN",
        allow_leading_dot=True,
    )
    if not host_is_within_cookie_domain(normalized_delivery, normalized_cookie):
        raise HLSDeliveryConfigurationError(
            "CLOUDFRONT_DOMAIN must equal or be a subdomain of "
            "CLOUDFRONT_COOKIE_DOMAIN"
        )

    normalized_request = None
    if request_host is not None:
        normalized_request = hostname_from_request_host(request_host)
        if not host_is_within_cookie_domain(normalized_request, normalized_cookie):
            raise HLSDeliveryConfigurationError(
                "The API response host cannot set CLOUDFRONT_COOKIE_DOMAIN"
            )

    return HLSCookieScope(
        delivery_host=normalized_delivery,
        cookie_domain=normalized_cookie,
        request_host=normalized_request,
    )


def allowed_host_supports_cookie_domain(host: object, cookie_domain: str) -> bool:
    """Return whether a concrete Django ALLOWED_HOST can set the cookie domain."""

    if not isinstance(host, str) or not host.strip() or host.strip() == "*":
        return False
    try:
        normalized = normalize_dns_name(
            host,
            setting_name="DJANGO_ALLOWED_HOSTS entry",
        )
    except HLSDeliveryConfigurationError:
        return False
    return host_is_within_cookie_domain(normalized, cookie_domain)


def _hls_path_segments(value: object, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value or value.startswith("/"):
        raise HLSDeliveryConfigurationError(
            f"{field_name} must be a relative storage path"
        )
    if "\\" in value or any(ord(character) < 32 for character in value):
        raise HLSDeliveryConfigurationError(
            f"{field_name} contains unsafe path characters"
        )
    segments = tuple(value.split("/"))
    if any(segment in {"", ".", ".."} for segment in segments):
        raise HLSDeliveryConfigurationError(
            f"{field_name} must be normalized and cannot contain traversal"
        )
    return segments


def resolve_hls_resource_scope(*, prefix: object, playlist_name: object) -> HLSResourceScope:
    """Require the returned playlist to be a strict child of the signed prefix."""

    prefix_segments = _hls_path_segments(prefix, field_name="HLS prefix")
    playlist_segments = _hls_path_segments(
        playlist_name,
        field_name="HLS playlist name",
    )
    if (
        len(playlist_segments) <= len(prefix_segments)
        or playlist_segments[: len(prefix_segments)] != prefix_segments
    ):
        raise HLSDeliveryConfigurationError(
            "HLS playlist name must be strictly under the signed HLS prefix"
        )

    encoded_prefix = "/".join(quote(segment, safe="-._~") for segment in prefix_segments)
    encoded_playlist = "/".join(
        quote(segment, safe="-._~") for segment in playlist_segments
    )
    return HLSResourceScope(
        policy_path=f"{encoded_prefix}/*",
        playlist_path=encoded_playlist,
        cookie_path=f"/{encoded_prefix}/",
    )


def normalize_cached_expiry(value: object) -> datetime | None:
    """Normalize legacy UTC expiries; return ``None`` for unusable cache data."""

    try:
        if isinstance(value, str):
            value = parse_datetime(value.strip())
        if not isinstance(value, datetime):
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    except Exception:
        return None


def has_valid_cloudfront_cookies(
    value: object,
    *,
    expected_key_pair_id: str | None = None,
) -> bool:
    """Require the complete custom-policy cookie triplet from the signer/cache."""

    if not isinstance(value, dict):
        return False
    try:
        valid = all(
            isinstance(value.get(name), str)
            and bool(value[name])
            and value[name].isascii()
            and all(32 < ord(character) < 127 for character in value[name])
            for name in CLOUDFRONT_COOKIE_NAMES
        )
        if not valid:
            return False
        return (
            expected_key_pair_id is None
            or value["CloudFront-Key-Pair-Id"] == expected_key_pair_id
        )
    except Exception:
        return False
