from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ChaptersConfig(AppConfig):
    name = 'apps.media.chapters'
    label = 'chapters'

    verbose_name = _('Chapters')
    verbose_name_plural = _('Chapters')

    namespace = 'chapters'