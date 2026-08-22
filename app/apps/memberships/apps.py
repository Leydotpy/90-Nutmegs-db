from django.utils.translation import gettext_lazy as _
from core.application import AppConfig


class MembershipsConfig(AppConfig):
    name = 'apps.memberships'
    label = 'memberships'
    verbose_name = _('Memberships')

    namespace = 'membership'

    def ready(self):
        from . import receivers # noqa
