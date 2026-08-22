"""Shared signing helpers for service-to-service promotion webhooks."""

from __future__ import annotations

import hashlib
import hmac
import time

CLIENT_HEADER = "X-SanFootball-Client"
TIMESTAMP_HEADER = "X-SanFootball-Timestamp"
SIGNATURE_HEADER = "X-SanFootball-Signature"
CHECKSUM_HEADER = "X-SanFootball-Content-SHA256"


def sha256_hexdigest(payload: bytes) -> str:
    """Return a hex SHA256 digest for the supplied payload."""
    return hashlib.sha256(payload).hexdigest()


def build_upload_signature(*, client_id: str, secret: str, method: str, path: str, timestamp: str, resource_id: str, checksum: str) -> str:
    """Build the canonical signature used for multipart upload requests."""
    canonical = "\n".join([client_id, method.upper(), path, timestamp, resource_id, checksum])
    return hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def build_signed_webhook_headers(*, payload: bytes, client_id: str, secret: str, timestamp: str | None = None) -> dict[str, str]:
    """Build signed headers for JSON webhooks exchanged between services."""
    resolved_timestamp = timestamp or str(int(time.time()))
    checksum = sha256_hexdigest(payload)
    signature = build_upload_signature(
        client_id=client_id,
        secret=secret,
        method="POST",
        path="webhook",
        timestamp=resolved_timestamp,
        resource_id="webhook",
        checksum=checksum,
    )
    return {
        CLIENT_HEADER: client_id,
        TIMESTAMP_HEADER: resolved_timestamp,
        CHECKSUM_HEADER: checksum,
        SIGNATURE_HEADER: signature,
    }


def verify_signed_webhook(*, payload: bytes, headers, secret: str, expected_client_id: str | None = None, max_age_seconds: int = 300) -> bool:
    """Verify a signed JSON webhook request."""
    client_id = headers.get(CLIENT_HEADER, "")
    timestamp = headers.get(TIMESTAMP_HEADER, "")
    checksum = headers.get(CHECKSUM_HEADER, "")
    signature = headers.get(SIGNATURE_HEADER, "")

    if not client_id or not timestamp or not checksum or not signature:
        return False
    if expected_client_id and client_id != expected_client_id:
        return False
    if checksum != sha256_hexdigest(payload):
        return False
    try:
        age = abs(int(time.time()) - int(timestamp))
    except ValueError:
        return False
    if age > max_age_seconds:
        return False

    expected_signature = build_upload_signature(
        client_id=client_id,
        secret=secret,
        method="POST",
        path="webhook",
        timestamp=timestamp,
        resource_id="webhook",
        checksum=checksum,
    )
    return hmac.compare_digest(expected_signature, signature)
