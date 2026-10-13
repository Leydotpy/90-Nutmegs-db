from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PersonsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.persons"
    label = "persons"
    verbose_name = _("Persons")

    def ready(self):
        from apps.persons import receivers  # noqa: F401
