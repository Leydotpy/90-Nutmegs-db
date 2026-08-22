from django.utils.translation import gettext_lazy as _
from core.application import AppConfig

class PodcastsConfig(AppConfig):
    name = "apps.posts.podcasts"
    label = "podcasts"
    verbose_name = _("Podcasts")

    namespace = "podcasts"

    def ready(self):
        from apps.posts.podcasts import receivers # noqa
        from api.rest.dashboard.apps.memberships.serializers import register_entitlement_serializer
        from api.rest.dashboard.apps.podcasts.serializers import PodcastModelSerializer, EpisodeModelSerializer

        register_entitlement_serializer("podcasts", "Podcast", PodcastModelSerializer)
        register_entitlement_serializer("podcasts", "Episode", EpisodeModelSerializer)
