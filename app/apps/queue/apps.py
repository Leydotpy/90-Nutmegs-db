from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QueueConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.queue"
    label = "queue"
    verbose_name = _("Queue")

    def ready(self):
        from . import signals  # noqa: F401
