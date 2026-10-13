"""Development settings with local, non-production-safe defaults."""

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import BASE_DIR
from .environment import config, csv_values

DEBUG = config("DJANGO_DEBUG", cast=bool, default=True)
SECRET_KEY = config(
    "DJANGO_SECRET_KEY",
    default="unsafe-sanfootball-development-key-do-not-deploy",
)
ALLOWED_HOSTS = [
    host.strip()
    for host in config(
        "DJANGO_ALLOWED_HOSTS",
        default="localhost,127.0.0.1,testserver",
    ).split(",")
    if host.strip()
]

CORS_ALLOWED_ORIGINS = csv_values(
    config(
        "CORS_ALLOWED_ORIGINS",
        default="http://localhost:3000,http://localhost:5173,http://localhost:8050",
    )
)
CSRF_TRUSTED_ORIGINS = csv_values(config("CSRF_TRUSTED_ORIGINS", default=""))

try:
    _database = dj_database_url.parse(
        config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=0,
    )
except ValueError, TypeError:
    raise ImproperlyConfigured("DATABASE_URL must be a valid database URL") from None
DATABASES = {"default": _database}

# Development starts without a Redis dependency. A developer may opt in
# explicitly without changing committed settings.
if config("USE_REDIS_CACHE", cast=bool, default=False):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/1"),
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "sanfootball-development",
        }
    }

SESSION_COOKIE_SECURE = False
PODCAST_QUEUE_SESSION_COOKIE_SECURE = False
RECENTLY_VIEWED_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
