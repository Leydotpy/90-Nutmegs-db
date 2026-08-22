# apps/media/webhook.py
import hashlib
import hmac
import json
import logging
import requests
from django.utils import timezone

logger = logging.getLogger(__name__)

def send_signed_webhook(callback_url: str, body: dict, secret: str, timeout: int = 5):
    """
    POST JSON body to callback_url with HMAC-SHA256 signature in header `X-Signature`.
    Returns (status_code, response_text) or raises on network errors.
    """
    payload = json.dumps(body, default=str).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-Signature": sig,
        "X-Hook-Timestamp": str(int(timezone.now().timestamp()))
    }
    try:
        resp = requests.post(callback_url, data=payload, headers=headers, timeout=timeout)
        return resp.status_code, resp.text
    except requests.RequestException as exc:
        logger.exception("Webhook POST failed: %s", exc)
        raise
