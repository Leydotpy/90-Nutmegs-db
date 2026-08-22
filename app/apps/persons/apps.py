from django.utils.translation import gettext_lazy as _
from core.application import AppConfig


class PersonsConfig(AppConfig):
    name = 'apps.persons'
    label = "persons"
    verbose_name = _("Persons")

    namespace = "persons"

    def ready(self):
        from apps.persons import receivers # noqa
