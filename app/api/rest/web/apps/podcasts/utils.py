from api.rest.web.apps.podcasts.serializers import AutomaticPodcastPromotionSerializer, \
    HandPickedPodcastPromotionSerializers
from apps.promotions.models import AutomaticPostList, HandPickedPostList


def get_module_serializer(view, serializer_class, *args, **kwargs):
    kwargs.setdefault("context", view.get_serializer_context())
    return serializer_class(*args, **kwargs)

def make_automatic_post_module(view):
    return get_module_serializer(
        view,
        AutomaticPodcastPromotionSerializer,
        AutomaticPostList.objects.all(),
        many=True
    ).data

def make_handpicked_module(view):
    return get_module_serializer(
        view,
        HandPickedPodcastPromotionSerializers,
        HandPickedPostList.objects.all(),
        many=True
    ).data
