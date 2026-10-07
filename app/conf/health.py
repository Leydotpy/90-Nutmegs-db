"""Minimal process, database, and cache probes for deployment orchestration."""

import logging
from uuid import uuid4

from django.core.cache import cache
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
def liveness(_request):
    """Confirm that the web process can serve requests; no dependency checks."""

    return JsonResponse({"status": "ok", "service": "90Nutmegs"})


@require_GET
def readiness(_request):
    """Confirm that the process can reach its database and critical cache."""

    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        # Keep the response and log free of driver/DSN details.
        logger.warning("Readiness database check failed")
        checks["database"] = "error"
    else:
        checks["database"] = "ok"

    cache_token = uuid4().hex
    cache_key = f"90Nutmegs:readiness:{cache_token}"
    try:
        cache.set(cache_key, cache_token, timeout=5)
        if cache.get(cache_key) != cache_token:
            raise RuntimeError("cache readiness round trip failed")
        cache.delete(cache_key)
    except Exception:
        logger.warning("Readiness cache check failed")
        checks["cache"] = "error"
    else:
        checks["cache"] = "ok"

    available = all(value == "ok" for value in checks.values())
    return JsonResponse(
        {"status": "ready" if available else "unavailable", "checks": checks},
        status=200 if available else 503,
    )
