from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MembershipsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.memberships"
    label = "memberships"
    verbose_name = _("Memberships")

    def ready(self):
        from . import receivers  # noqa: F401
