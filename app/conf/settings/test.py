"""Deterministic settings for the repository test suite."""

from .base import *  # noqa: F401,F403

DEBUG = False
SECRET_KEY = "sanfootball-test-key-not-for-deployment"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "90Nutmegs-tests",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# Tests never contact identity, AI, storage, or signing providers unless a
# provider-contract test injects an explicit fake adapter.
CLERK_SECRET_KEY = "test-clerk-secret"
OPENAI_API_KEY = ""
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
MEDIA_BUCKET = ""
CLOUDFRONT_KEY_PAIR_ID = ""
CLOUDFRONT_PRIVATE_KEY = ""
MEDIA_STORAGE_PROVIDER = "local"
IMAGE_PLATFORM_PROVIDER = "disabled"
VIDEO_PLATFORM_PROVIDER = "disabled"
CLOUDFLARE_ACCOUNT_ID = ""
CLOUDFLARE_API_TOKEN = ""
R2_ACCESS_KEY_ID = ""
R2_SECRET_ACCESS_KEY = ""
R2_PRIVATE_BUCKET_NAME = ""
R2_PUBLIC_BUCKET_NAME = ""
R2_PUBLIC_BASE_URL = ""
MEDIA_FILEFIELD_R2_CUTOVER_CONFIRMED = False
CLOUDFLARE_IMAGES_ACCOUNT_HASH = ""
CLOUDFLARE_IMAGES_SIGNING_KEY = ""
CLOUDFLARE_STREAM_CUSTOMER_CODE = ""
CLOUDFLARE_STREAM_SIGNING_KEY_ID = ""
CLOUDFLARE_STREAM_SIGNING_PRIVATE_KEY_B64 = ""
CLOUDFLARE_STREAM_WEBHOOK_SECRET = ""
MEDIA_UPLOAD_ALLOWED_ORIGINS = ()
CLOUDFLARE_STREAM_ALLOWED_ORIGINS = ()
