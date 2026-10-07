# apps/media/webhook.py
import hashlib
import hmac
import json
import logging
from urllib.parse import urlsplit

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

logger = logging.getLogger(__name__)


def _origin(url: str) -> str:
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except (TypeError, ValueError) as exc:
        raise ValidationError("Invalid offline callback URL.") from exc

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise ValidationError("Invalid offline callback URL.")
    if not settings.DEBUG and parsed.scheme != "https":
        raise ValidationError("Offline callbacks must use HTTPS.")

    default_port = 443 if parsed.scheme == "https" else 80
    port_suffix = f":{port}" if port is not None and port != default_port else ""
    return f"{parsed.scheme}://{parsed.hostname.lower()}{port_suffix}"


def validate_callback_url(callback_url: str) -> str:
    """Allow a callback only when its exact origin is configured by operators."""

    origin = _origin(callback_url)
    allowed_origins = {
        _origin(allowed)
        for allowed in getattr(settings, "OFFLINE_WEBHOOK_ALLOWED_ORIGINS", ())
    }
    if origin not in allowed_origins:
        raise ValidationError("Offline callback origin is not allowed.")
    return callback_url


def send_signed_webhook(callback_url: str, body: dict, secret: str, timeout: int = 5):
    """
    POST JSON body to callback_url with HMAC-SHA256 signature in header `X-Signature`.
    Returns (status_code, response_text) or raises on network errors.
    """
    callback_url = validate_callback_url(callback_url)
    payload = json.dumps(body, default=str).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-Signature": sig,
        "X-Hook-Timestamp": str(int(timezone.now().timestamp()))
    }
    try:
        resp = requests.post(
            callback_url,
            data=payload,
            headers=headers,
            timeout=timeout,
            allow_redirects=False,
        )
        return resp.status_code, resp.text
    except requests.RequestException:
        # Request exceptions may include callback query strings or credentials;
        # keep operational logs free of endpoint details.
        logger.exception("Offline webhook POST failed")
        raise
