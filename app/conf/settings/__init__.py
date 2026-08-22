"""
Django settings loader.

This module is the main settings entry point for the project.

It composes settings from multiple files in a predictable order:

    base.py        -> shared project defaults
    production.py  -> production/deployment configuration
    local.py       -> optional developer-specific overrides

The import order is intentional. Later imports override values imported earlier.
Therefore, ``production.py`` may override values from ``base.py``, and
``local.py`` may override both ``base.py`` and ``production.py``.

This design allows the project to remain production-ready by default while also
supporting local development without requiring changes to committed settings
files.

Expected files:

    base.py
        Shared settings used by every environment.

    production.py
        Deployment-safe settings used when no local override is present.

    local.py
        Optional file for developer-specific configuration. This file is usually
        ignored by version control and may contain local database settings,
        debugging flags, test credentials, local broker URLs, or development
        tools.

Example local.py:

    DEBUG = True

    ALLOWED_HOSTS = [
        "localhost",
        "127.0.0.1",
    ]

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "my_project",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "HOST": "localhost",
            "PORT": "5432",
        }
    }

Security note:
    Production secrets should not be hardcoded in settings files. Use
    environment variables for sensitive values such as ``SECRET_KEY``, database
    credentials, email passwords, payment keys, Celery broker URLs, and external
    service credentials.

Operational note:
    If ``local.py`` is absent, the project will continue to run using the base
    and production settings. This is expected behaviour and should not be
    treated as a fatal error.
"""

import logging


logger = logging.getLogger(__name__)

from .base import *  # noqa: F403
# from .production import *  # noqa: F403


LOCAL_SETTINGS_PATH = Path(__file__).with_name("local.py")

if LOCAL_SETTINGS_PATH.exists():
    from .local import *  # noqa: F403

    logger.info(
        "Local settings file successfully loaded from %s. The project is now "
        "running with development/local configuration overrides applied on top of "
        "the shared base settings and production defaults. This usually indicates "
        "that the application is being executed in a local development environment, "
        "where developer-specific settings may override values such as DEBUG, "
        "DATABASES, ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, EMAIL_BACKEND, CACHE "
        "configuration, Celery broker and result backend URLs, logging preferences, "
        "test credentials, and other machine-specific runtime options.",
        LOCAL_SETTINGS_PATH,
    )
else:
    logger.warning(
        "No local settings file was found at %s. The project is running with "
        "production settings applied, together with the shared base settings, and "
        "no local developer-specific overrides have been loaded for this runtime. "
        "This means the application is operating under the production-oriented "
        "configuration path. If you are running the project on your development "
        "machine, consider creating a local.py file in the settings package to "
        "override development-specific values such as DEBUG, DATABASES, "
        "ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, EMAIL_BACKEND, CACHE configuration, "
        "Celery broker and result backend URLs, logging preferences, test "
        "credentials, and other machine-specific settings. If this is a staging "
        "or production deployment, this behaviour is expected provided that "
        "production.py and the required environment variables fully define the "
        "runtime configuration.",
        LOCAL_SETTINGS_PATH,
    )