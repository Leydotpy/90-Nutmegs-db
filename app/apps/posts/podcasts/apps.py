from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PodcastsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.posts.podcasts"
    label = "podcasts"
    verbose_name = _("Podcasts")

    def ready(self):
        from apps.posts.podcasts import receivers  # noqa: F401
