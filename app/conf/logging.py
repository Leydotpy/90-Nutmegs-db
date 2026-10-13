"""Last-mile redaction for configured log handlers.

Callers must still log event metadata instead of credentials, request bodies or
capabilities. This formatter protects common accidental disclosures, including
exception/stack output. It cannot classify arbitrary unlabelled private data.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from copy import copy
from urllib.parse import parse_qsl, quote, quote_plus, unquote, urlsplit

from django.conf import settings

REDACTED = "[REDACTED]"
_SENSITIVE_NAMES = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "key",
    "api_key",
    "authorization",
    "proxy_authorization",
    "cookie",
    "set_cookie",
    "credentials",
    "private_key",
    "private_key_b64",
    "secret_key",
    "signing_key",
    "data_key",
    "access_key",
    "access_key_id",
    "signature",
    "webhook_payload",
    "webhook_body",
    "payment_payload",
    "payment_data",
    "signed_url",
    "upload_url",
    "playback_url",
    "x_api_key",
    "x_auth_token",
}
_SENSITIVE_SUFFIXES = (
    "_password",
    "_passwd",
    "_secret",
    "_token",
    "_api_key",
    "_private_key",
    "_private_key_b64",
    "_secret_key",
    "_signing_key",
    "_access_key",
    "_access_key_id",
    "_signature",
    "_webhook_payload",
    "_webhook_body",
)
_PEM = re.compile(
    r"-----BEGIN (?P<label>(?:[A-Z0-9]+ )*PRIVATE KEY)-----.*?"
    r"-----END (?P=label)-----",
    re.DOTALL,
)
_URL = re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s<>\"']+", re.IGNORECASE)
_JWT_PATH = re.compile(r"(?:^|/)eyJ[\w-]+\.[\w-]+\.[\w-]+(?:/|$)")
_AUTH = re.compile(r"\b(Bearer|Basic)\s+[^\s,;\"'<>]+", re.IGNORECASE)
_FIELD = re.compile(
    r"(?<![\w-])(?:[\"']?)(?P<name>webhook[ ](?:payload|body)|[a-z][\w-]*)"
    r"(?:[\"']?)\s*[:=]\s*",
    re.IGNORECASE,
)
_NEXT_FIELD = re.compile(r"\s+(?=[\"']?[a-z][\w-]*[\"']?\s*[:=])", re.IGNORECASE)


def _sensitive_name(name: str) -> bool:
    normalized = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    normalized = normalized.lower().replace("-", "_").replace(" ", "_")
    return normalized in _SENSITIVE_NAMES or normalized.endswith(_SENSITIVE_SUFFIXES)


def _secret_strings(value: object, *, sensitive: bool = False):
    """Read only canonical settings, including nested backend passwords."""
    if isinstance(value, str):
        if sensitive and value:
            yield value
        if "://" in value:
            try:
                password = urlsplit(value).password
            except ValueError:
                return
            if password:
                yield unquote(password)
    elif isinstance(value, Mapping):
        for key, child in value.items():
            yield from _secret_strings(child, sensitive=sensitive or _sensitive_name(str(key)))
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _secret_strings(child, sensitive=sensitive)


def _configured_secrets() -> set[str]:
    # Re-read on each record: overrides and rotated/injected settings must not
    # leave stale redaction rules. There is no environment dump or network I/O.
    if not settings.configured:
        return set()
    secrets = set()
    for name in dir(settings):
        if _sensitive_name(name) or name == "SECRET_KEY_FALLBACKS":
            secrets.update(_secret_strings(getattr(settings, name), sensitive=True))
    for name in (
        "DATABASES",
        "CACHES",
        "STORAGES",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "REDIS_URL",
        "DATABASE_URL",
    ):
        secrets.update(_secret_strings(getattr(settings, name, None)))
    return secrets


def _redact_url(match: re.Match[str]) -> str:
    value = match.group()
    try:
        parsed = urlsplit(value)
        query_names = {name for name, _ in parse_qsl(parsed.query)}
        if (
            parsed.username is not None
            or parsed.password is not None
            or any(_sensitive_name(name) for name in query_names)
            or {name.lower().replace("-", "_") for name in query_names}
            & {
                "sig",
                "jwt",
                "auth",
                "hmac",
                "policy",
                "key_pair_id",
                "x_amz_credential",
                "x_goog_credential",
            }
            or _JWT_PATH.search(unquote(parsed.path))
            or parsed.hostname in {"upload.videodelivery.net", "upload.imagedelivery.net"}
        ):
            return REDACTED
    except ValueError:
        # A malformed credential URL must not escape redaction because parsing
        # failed (for example, an invalid IPv6 authority).
        if "@" in value or "?" in value:
            return REDACTED
    return value


def _value_end(text: str, start: int) -> int:
    """Consume a quoted/structured field, including nested webhook reprs."""
    position = start
    if text[position : position + 1] in {"b", "r", "u"}:
        position += 1
    if text[position : position + 1] in {"'", '"'}:
        delimiter = text[position]
        position += 1
        while position < len(text):
            if text[position] == "\\":
                position += 2
                continue
            if text[position] == delimiter:
                return position + 1
            position += 1
        return len(text)
    if text[start : start + 1] in {"{", "[", "("}:
        closers = {"{": "}", "[": "]", "(": ")"}
        stack = [closers[text[start]]]
        position = start + 1
        while position < len(text):
            character = text[position]
            if character in {"'", '"'}:
                position = _value_end(text, position)
                continue
            if character in closers:
                stack.append(closers[character])
            elif character == stack[-1]:
                stack.pop()
                if not stack:
                    return position + 1
            position += 1
        return len(text)
    # Unquoted multiword values run to a delimiter or the next named field.
    # Do not expose the tail merely because a password contains whitespace.
    boundary = re.search(r"[,;\n\r}\])]|\s+$", text[start:])
    end = start + boundary.start() if boundary else len(text)
    next_field = _NEXT_FIELD.search(text, start, end)
    return next_field.start() if next_field else end


def _redact_fields(text: str) -> str:
    output = []
    position = 0
    for match in _FIELD.finditer(text):
        if match.start() < position or not _sensitive_name(match["name"]):
            continue
        output.append(text[position : match.end()])
        output.append(REDACTED)
        position = _value_end(text, match.end())
    output.append(text[position:])
    return "".join(output)


class RedactingFormatter(logging.Formatter):
    """Redact the final rendered text without modifying a shared LogRecord."""

    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(copy(record))
        variants = set()
        for secret in _configured_secrets():
            variants.update(
                (
                    secret,
                    repr(secret)[1:-1],
                    json.dumps(secret)[1:-1],
                    quote(secret),
                    quote(secret, safe=""),
                    quote_plus(secret),
                )
            )
        for secret in sorted(variants, key=len, reverse=True):
            rendered = rendered.replace(secret, REDACTED)
        rendered = _PEM.sub(REDACTED, rendered)
        rendered = _URL.sub(_redact_url, rendered)
        rendered = _AUTH.sub(lambda match: f"{match[1]} {REDACTED}", rendered)
        return _redact_fields(rendered)
