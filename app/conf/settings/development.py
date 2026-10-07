"""Development settings with local, non-production-safe defaults."""

import dj_database_url
from decouple import config

from .base import *  # noqa: F401,F403
from .base import BASE_DIR

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

DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=0,
    )
}

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
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
