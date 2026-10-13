"""Celery routing shared by producers and independently deployed worker pools."""

from kombu import Queue

# Keep the historical default queue so ordinary messages survive a rolling upgrade.
DEFAULT_QUEUE = "celery"
MEDIA_QUEUE = "media"
BULK_QUEUE = "bulk"

TASK_QUEUES = tuple(
    Queue(name, routing_key=name) for name in (DEFAULT_QUEUE, MEDIA_QUEUE, BULK_QUEUE)
)
TASK_ROUTES = {
    "Audio Processing Pipeline": {"queue": MEDIA_QUEUE},
    "apps.media.offline.tasks.build_offline_package_streaming": {"queue": MEDIA_QUEUE},
    "apps.media.offline.tasks.build_offline_package_task": {"queue": MEDIA_QUEUE},
    "CloudFront Audio HLS Signing Task": {"queue": DEFAULT_QUEUE},
    "Recalculate Trending Episodes": {"queue": BULK_QUEUE},
    "apps.recommendation.tasks.recalc_user_category_affinity_postgres": {"queue": BULK_QUEUE},
    "conf.tasks.expire_offline_licenses": {"queue": DEFAULT_QUEUE},
    "conf.tasks.revoke_inactive_devices": {"queue": DEFAULT_QUEUE},
    "conf.tasks.collect_orphaned_packages": {"queue": BULK_QUEUE},
}

BEAT_SCHEDULE = {
    # Retain this historical key (and its daily interval) to avoid duplicating
    # an existing django-celery-beat row during rollout.
    "recalc-user-category-affinity-every-10-min": {
        "task": "apps.recommendation.tasks.recalc_user_category_affinity_postgres",
        "schedule": 24 * 3600,
    },
    "expire-licenses-daily": {
        "task": "conf.tasks.expire_offline_licenses",
        "schedule": 24 * 3600,
    },
    "rotate-cloud-front-cookies": {
        "task": "CloudFront Audio HLS Signing Task",
        "schedule": 24 * 3600,
    },
    "revoke-inactive-devices-weekly": {
        "task": "conf.tasks.revoke_inactive_devices",
        "schedule": 7 * 24 * 3600,
    },
    "gc-orphan-packages-daily": {
        "task": "conf.tasks.collect_orphaned_packages",
        "schedule": 24 * 3600,
    },
}
