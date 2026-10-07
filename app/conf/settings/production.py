"""Production settings selected explicitly by deployed processes."""

import dj_database_url
from apps.media.delivery import (
    HLSDeliveryConfigurationError,
    allowed_host_supports_cookie_domain,
    resolve_hls_cookie_scope,
)
from apps.media.providers.config import CloudflareMediaConfig
from decouple import config
from django.core.exceptions import ImproperlyConfigured
from pycflare.django import r2_storages
from pycflare.storage import R2Settings

from . import base as base_settings
from .base import *  # noqa: F401,F403

# Name the inherited values used by production-only validation explicitly so
# static checks can prove they exist despite the transitional wildcard import.
CLOUDFRONT_DOMAIN = base_settings.CLOUDFRONT_DOMAIN
CLOUDFRONT_COOKIE_DOMAIN = base_settings.CLOUDFRONT_COOKIE_DOMAIN
CLOUDFRONT_KEY_PAIR_ID = base_settings.CLOUDFRONT_KEY_PAIR_ID
CLOUDFRONT_PRIVATE_KEY = base_settings.CLOUDFRONT_PRIVATE_KEY
CLOUDFRONT_COOKIE_TTL = base_settings.CLOUDFRONT_COOKIE_TTL
CLOUDFRONT_SIGN_CACHE_TIMEOUT_MARGIN = base_settings.CLOUDFRONT_SIGN_CACHE_TIMEOUT_MARGIN
MEDIA_UPLOAD_URL_TTL_SECONDS = base_settings.MEDIA_UPLOAD_URL_TTL_SECONDS
MEDIA_PRIVATE_URL_TTL_SECONDS = base_settings.MEDIA_PRIVATE_URL_TTL_SECONDS
MEDIA_UPLOAD_MAX_BYTES = base_settings.MEDIA_UPLOAD_MAX_BYTES
MEDIA_UPLOAD_MAX_DURATION_SECONDS = base_settings.MEDIA_UPLOAD_MAX_DURATION_SECONDS


def _required(name: str) -> str:
    value = config(name, default="").strip()
    if not value:
        raise ImproperlyConfigured(f"{name} is required by conf.settings.production")
    return value


DEBUG = False
SECRET_KEY = _required("DJANGO_SECRET_KEY")
if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must contain at least 50 characters in production"
    )

ALLOWED_HOSTS = [
    host.strip() for host in _required("DJANGO_ALLOWED_HOSTS").split(",") if host.strip()
]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must contain at least one allowed host")
if "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS cannot contain the global '*' wildcard in production"
    )
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in config("CORS_ALLOWED_ORIGINS", default="").split(",")
    if origin.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in config("CSRF_TRUSTED_ORIGINS", default="").split(",")
    if origin.strip()
]

DATABASE_URL = _required("DATABASE_URL")
DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=config("DATABASE_CONN_MAX_AGE", cast=int, default=60),
        conn_health_checks=True,
    )
}
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise ImproperlyConfigured("DATABASE_URL must use PostgreSQL in conf.settings.production")

REDIS_URL = _required("REDIS_URL")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Access decisions never trust cache state. Treat outages as misses
            # so Clerk can verify bearer tokens at the provider, while the
            # readiness probe removes the instance from service.
            "IGNORE_EXCEPTIONS": True,
        },
    }
}
CELERY_BROKER_URL = _required("CELERY_BROKER_URL")
CLERK_SECRET_KEY = _required("CLERK_SECRET_KEY")
CLERK_AUTH_PARTIES = tuple(
    party.strip() for party in _required("CLERK_AUTH_PARTIES").split(",") if party.strip()
)
if not CLERK_AUTH_PARTIES:
    raise ImproperlyConfigured("CLERK_AUTH_PARTIES must contain at least one allowed party")
GIFFY_SHARED_SECRET = _required("GIFFY_SHARED_SECRET")
if len(GIFFY_SHARED_SECRET) < 32:
    raise ImproperlyConfigured(
        "GIFFY_SHARED_SECRET must contain at least 32 characters in production"
    )

MEDIA_STORAGE_PROVIDER = config(
    "MEDIA_STORAGE_PROVIDER",
    default="cloudflare_r2",
).strip()
IMAGE_PLATFORM_PROVIDER = config(
    "IMAGE_PLATFORM_PROVIDER",
    default="cloudflare_images",
).strip()
VIDEO_PLATFORM_PROVIDER = config(
    "VIDEO_PLATFORM_PROVIDER",
    default="cloudflare_stream",
).strip()
_selected_media_providers = {
    "MEDIA_STORAGE_PROVIDER": (MEDIA_STORAGE_PROVIDER, "cloudflare_r2"),
    "IMAGE_PLATFORM_PROVIDER": (IMAGE_PLATFORM_PROVIDER, "cloudflare_images"),
    "VIDEO_PLATFORM_PROVIDER": (VIDEO_PLATFORM_PROVIDER, "cloudflare_stream"),
}
for _provider_setting, (_actual_provider, _required_provider) in _selected_media_providers.items():
    if _actual_provider != _required_provider:
        raise ImproperlyConfigured(
            f"{_provider_setting} must be {_required_provider!r} in production"
        )

CLOUDFLARE_ACCOUNT_ID = _required("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = _required("CLOUDFLARE_API_TOKEN")
R2_ACCESS_KEY_ID = _required("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = _required("R2_SECRET_ACCESS_KEY")
R2_PRIVATE_BUCKET_NAME = _required("R2_PRIVATE_BUCKET_NAME")
R2_PUBLIC_BUCKET_NAME = _required("R2_PUBLIC_BUCKET_NAME")
R2_PUBLIC_BASE_URL = _required("R2_PUBLIC_BASE_URL")
_media_filefield_cutover_confirmation = _required("MEDIA_FILEFIELD_R2_CUTOVER_CONFIRMED").lower()
MEDIA_FILEFIELD_R2_CUTOVER_CONFIRMED = _media_filefield_cutover_confirmation in {
    "1",
    "true",
    "yes",
    "on",
}
if not MEDIA_FILEFIELD_R2_CUTOVER_CONFIRMED:
    raise ImproperlyConfigured(
        "MEDIA_FILEFIELD_R2_CUTOVER_CONFIRMED must be true only after legacy "
        "FileField objects have been copied to the private R2 bucket and reconciled"
    )
CLOUDFLARE_IMAGES_ACCOUNT_HASH = _required("CLOUDFLARE_IMAGES_ACCOUNT_HASH")
CLOUDFLARE_IMAGES_SIGNING_KEY = _required("CLOUDFLARE_IMAGES_SIGNING_KEY")
CLOUDFLARE_STREAM_CUSTOMER_CODE = _required("CLOUDFLARE_STREAM_CUSTOMER_CODE")
CLOUDFLARE_STREAM_SIGNING_KEY_ID = _required("CLOUDFLARE_STREAM_SIGNING_KEY_ID")
CLOUDFLARE_STREAM_SIGNING_PRIVATE_KEY_B64 = _required("CLOUDFLARE_STREAM_SIGNING_PRIVATE_KEY_B64")
CLOUDFLARE_STREAM_WEBHOOK_SECRET = _required("CLOUDFLARE_STREAM_WEBHOOK_SECRET")
MEDIA_UPLOAD_ALLOWED_ORIGINS = tuple(
    origin.strip().rstrip("/")
    for origin in _required("MEDIA_UPLOAD_ALLOWED_ORIGINS").split(",")
    if origin.strip()
)
if not MEDIA_UPLOAD_ALLOWED_ORIGINS:
    raise ImproperlyConfigured(
        "MEDIA_UPLOAD_ALLOWED_ORIGINS must contain at least one HTTPS origin"
    )
CLOUDFLARE_STREAM_ALLOWED_ORIGINS = tuple(
    origin.strip().lower().rstrip(".")
    for origin in _required("CLOUDFLARE_STREAM_ALLOWED_ORIGINS").split(",")
    if origin.strip()
)
if not CLOUDFLARE_STREAM_ALLOWED_ORIGINS:
    raise ImproperlyConfigured(
        "CLOUDFLARE_STREAM_ALLOWED_ORIGINS must contain at least one playback hostname"
    )

CLOUDFLARE_MEDIA_CONFIG = CloudflareMediaConfig(
    account_id=CLOUDFLARE_ACCOUNT_ID,
    api_token=CLOUDFLARE_API_TOKEN,
    r2_access_key_id=R2_ACCESS_KEY_ID,
    r2_secret_access_key=R2_SECRET_ACCESS_KEY,
    r2_private_bucket_name=R2_PRIVATE_BUCKET_NAME,
    r2_public_bucket_name=R2_PUBLIC_BUCKET_NAME,
    r2_public_base_url=R2_PUBLIC_BASE_URL,
    images_account_hash=CLOUDFLARE_IMAGES_ACCOUNT_HASH,
    images_signing_key=CLOUDFLARE_IMAGES_SIGNING_KEY,
    stream_customer_code=CLOUDFLARE_STREAM_CUSTOMER_CODE,
    stream_signing_key_id=CLOUDFLARE_STREAM_SIGNING_KEY_ID,
    stream_signing_private_key_b64=CLOUDFLARE_STREAM_SIGNING_PRIVATE_KEY_B64,
    stream_webhook_secret=CLOUDFLARE_STREAM_WEBHOOK_SECRET,
    upload_url_ttl_seconds=MEDIA_UPLOAD_URL_TTL_SECONDS,
    private_url_ttl_seconds=MEDIA_PRIVATE_URL_TTL_SECONDS,
    upload_max_bytes=MEDIA_UPLOAD_MAX_BYTES,
    upload_max_duration_seconds=MEDIA_UPLOAD_MAX_DURATION_SECONDS,
    allowed_upload_origins=MEDIA_UPLOAD_ALLOWED_ORIGINS,
    stream_allowed_origins=CLOUDFLARE_STREAM_ALLOWED_ORIGINS,
)

# Existing FileFields become durable/private R2 objects in production.  Public
# canonical assets use the separately validated R2 custom domain through the
# provider adapter; keeping this default backend private avoids exposing legacy
# premium paths merely because they are FileFields.
_django_r2_settings = R2Settings(
    account_id=CLOUDFLARE_ACCOUNT_ID,
    access_key_id=R2_ACCESS_KEY_ID,
    secret_access_key=R2_SECRET_ACCESS_KEY,
    bucket_name=R2_PRIVATE_BUCKET_NAME,
    signed_url_expiry=MEDIA_PRIVATE_URL_TTL_SECONDS,
)
STORAGES = r2_storages(
    media_options={
        "settings": _django_r2_settings,
        "location": "media",
        "querystring_auth": True,
        "file_overwrite": False,
    },
    include_static=False,
)
STORAGES["staticfiles"] = {
    "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
}

# Signed HLS cookies are optional, but partial or undeliverable configuration is
# unsafe. The API response host and custom CDN hostname must share one explicit,
# narrow cookie domain; a browser cannot accept a cookie for an unrelated host.
_cloudfront_signing_values = {
    "CLOUDFRONT_DOMAIN": CLOUDFRONT_DOMAIN,
    "CLOUDFRONT_COOKIE_DOMAIN": CLOUDFRONT_COOKIE_DOMAIN,
    "CLOUDFRONT_KEY_PAIR_ID": CLOUDFRONT_KEY_PAIR_ID,
    "CLOUDFRONT_PRIVATE_KEY": CLOUDFRONT_PRIVATE_KEY,
}
if any(str(value).strip() for value in _cloudfront_signing_values.values()):
    missing_cloudfront_settings = [
        name for name, value in _cloudfront_signing_values.items() if not str(value).strip()
    ]
    if missing_cloudfront_settings:
        raise ImproperlyConfigured(
            "Signed HLS configuration is incomplete; missing "
            + ", ".join(missing_cloudfront_settings)
        )
    try:
        _hls_cookie_scope = resolve_hls_cookie_scope(
            delivery_host=CLOUDFRONT_DOMAIN,
            cookie_domain=CLOUDFRONT_COOKIE_DOMAIN,
        )
    except HLSDeliveryConfigurationError as exc:
        raise ImproperlyConfigured(str(exc)) from exc
    CLOUDFRONT_DOMAIN = _hls_cookie_scope.delivery_host
    CLOUDFRONT_COOKIE_DOMAIN = _hls_cookie_scope.cookie_domain
    if any("*" in host or host.startswith(".") for host in ALLOWED_HOSTS):
        raise ImproperlyConfigured(
            "Signed HLS requires DJANGO_ALLOWED_HOSTS to contain only concrete "
            "hostnames (no wildcards)"
        )
    if not any(
        allowed_host_supports_cookie_domain(host, CLOUDFRONT_COOKIE_DOMAIN)
        for host in ALLOWED_HOSTS
    ):
        raise ImproperlyConfigured(
            "DJANGO_ALLOWED_HOSTS must include a concrete API hostname that can "
            "set CLOUDFRONT_COOKIE_DOMAIN"
        )
    if CLOUDFRONT_COOKIE_TTL <= 0:
        raise ImproperlyConfigured("CLOUDFRONT_COOKIE_TTL must be greater than zero")
    if not 0 <= CLOUDFRONT_SIGN_CACHE_TIMEOUT_MARGIN < CLOUDFRONT_COOKIE_TTL:
        raise ImproperlyConfigured(
            "CLOUDFRONT_SIGN_CACHE_TIMEOUT_MARGIN must be non-negative and less "
            "than CLOUDFRONT_COOKIE_TTL"
        )

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", cast=bool, default=True)
# Container/orchestrator probes commonly reach the app over private HTTP rather
# than through the TLS-terminating proxy. Exempt only these two exact paths.
SECURE_REDIRECT_EXEMPT = [r"^health/(?:live|ready)/$"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", cast=int, default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    cast=bool,
    default=True,
)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", cast=bool, default=True)
