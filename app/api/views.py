import collections

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


def podcast_urls(request, format):
    return collections.OrderedDict([
        ("auto", reverse("podcast_web_api:auto", request=request, format=format)),
        ("handpicked", reverse("podcast_web_api:handpicked", request=request, format=format)),
        ("promotions", reverse("podcast_web_api:promotions", request=request, format=format)),
        ("trending", reverse("podcast_web_api:trending", request=request, format=format)),
        ("recently_viewed", reverse("podcast_web_api:recently-viewed", request=request, format=format)),
        ("recently_played", reverse("podcast_web_api:recently-played", request=request, format=format)),
        ("resume_playback", reverse("podcast_web_api:resume-playback", request=request, format=format)),
    ])


def profile_apis(request, format):
    return collections.OrderedDict([
        ("featured-playlists", reverse("profile_web_api:featured-playlist", request=request, format=format)),
        ("playlists", reverse("profile_web_api:add-to-playlist", request=request, format=format)),
    ])


def queue_apis(request, format):
    return collections.OrderedDict([
        ("queue", reverse("queue_web_api:detail", request=request, format=format)),
        ("add", reverse("queue_web_api:queue-add", request=request, format=format)),
        ("clear", reverse("queue_web_api:queue-clear", request=request, format=format)),
    ])


@api_view(["GET"])
def api_root(request, format=None, *args, **kwargs):
    apis = collections.OrderedDict(**podcast_urls(request, format), **profile_apis(request, format),
                                   **queue_apis(request, format))
    return Response(apis)
