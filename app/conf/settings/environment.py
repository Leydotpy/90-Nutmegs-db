"""Canonical environment parsing and value-free startup validation errors."""

import ipaddress
import math
import re
from urllib.parse import parse_qsl, urlsplit

from decouple import UndefinedValueError, undefined
from decouple import config as read_environment
from django.core.exceptions import ImproperlyConfigured


def config(name, default=undefined, cast=undefined):
    """Keep environment-over-dotenv precedence without echoing invalid values."""
    try:
        return read_environment(name, default=default, cast=cast)
    except UndefinedValueError, ValueError, TypeError:
        raise ImproperlyConfigured(f"{name} is missing or has an invalid value") from None


def csv_values(value):
    return [part.strip() for part in value.split(",") if part.strip()]


def allowed_hosts(value):
    hosts = csv_values(value)
    if not hosts:
        raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must contain at least one allowed host")
    if "*" in hosts:
        raise ImproperlyConfigured(
            "DJANGO_ALLOWED_HOSTS cannot contain the global '*' wildcard in production"
        )
    for host in hosts:
        valid = False
        if host.startswith("[") and host.endswith("]"):
            try:
                ipaddress.IPv6Address(host[1:-1])
                valid = True
            except ValueError:
                pass
        else:
            candidate = host.removeprefix(".").removesuffix(".")
            valid = len(candidate) <= 253 and re.fullmatch(
                r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
                r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*",
                candidate,
            )
        if not valid:
            raise ImproperlyConfigured(
                "DJANGO_ALLOWED_HOSTS entries must be hostnames or IP addresses, "
                "without schemes, ports, paths or wildcard characters"
            )
    return hosts


def https_origins(name, values):
    """Production browser trust lists contain exact HTTPS origins only."""
    origins = []
    for value in values:
        try:
            parsed = urlsplit(value)
            port = parsed.port
            valid = (
                parsed.scheme == "https"
                and parsed.hostname
                and not parsed.username
                and not parsed.password
                and parsed.path in {"", "/"}
                and not parsed.query
                and not parsed.fragment
                and "*" not in value
                and not any(character.isspace() for character in value)
                and (port is None or 1 <= port <= 65535)
            )
            if valid:
                # Reuse host syntax validation, without echoing its field name.
                hostname = parsed.hostname
                allowed_hosts(f"[{hostname}]" if ":" in hostname else hostname)
        except ValueError, ImproperlyConfigured:
            valid = False
        if not valid:
            raise ImproperlyConfigured(
                f"{name} must contain exact HTTPS origins without credentials, paths or wildcards"
            )
        origins.append(value.rstrip("/"))
    return origins


def service_url(name, value, schemes):
    """Validate a network service URL without connecting or revealing a DSN."""
    try:
        parsed = urlsplit(value)
        port = parsed.port
        valid = (
            parsed.scheme in schemes
            and parsed.hostname
            and not parsed.fragment
            and not any(character.isspace() for character in value)
            and (port is None or 1 <= port <= 65535)
        )
        if valid:
            hostname = parsed.hostname
            allowed_hosts(f"[{hostname}]" if ":" in hostname else hostname)
            if parsed.scheme in {"redis", "rediss"} and parsed.path not in {"", "/"}:
                valid = bool(re.fullmatch(r"/\d+", parsed.path))
            if parsed.scheme in {"redis", "rediss"}:
                valid = valid and all(
                    re.fullmatch(r"[0-9]+", item)
                    for key, item in parse_qsl(parsed.query, keep_blank_values=True)
                    if key == "db"
                )
    except ValueError, ImproperlyConfigured:
        valid = False
    if not valid:
        raise ImproperlyConfigured(f"{name} must be a valid {'/'.join(schemes)} service URL")
    return value


def nonnegative(name, value):
    if value < 0:
        raise ImproperlyConfigured(f"{name} must be non-negative")
    return value


def positive(name, value):
    if not math.isfinite(value) or value <= 0:
        raise ImproperlyConfigured(f"{name} must be finite and greater than zero")
    return value
