from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LeaguesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.region.leagues"
    label = "leagues"
    verbose_name = _("Leagues")

    def ready(self):
        from apps.region.leagues import receivers  # noqa: F401
