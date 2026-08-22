from django.utils.translation import gettext_lazy as _
from core.application import AppConfig



class QueueConfig(AppConfig):
    name = 'apps.queue'
    label = 'queue'
    verbose_name = _("Queue")

    namespace = 'Queue'

    def ready(self):
        from . import signals