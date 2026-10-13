from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ClubsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.region.leagues.clubs"
    label = "clubs"
    verbose_name = _("Clubs")

    def ready(self):
        from apps.region.leagues.clubs import receivers  # noqa: F401
