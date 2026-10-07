from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.cache import cache

from apps.posts.podcasts.queries import (trending_episodes, new_releases, editor_picked_episodes,
                               top_playlists, personalized_recommendations, trending_podcasts)
from api.rest.web.apps.podcasts.serializers import EpisodeListSerializer, PodcastListSerializer
from api.rest.web.serializers.category import CategorySerializer
from api.rest.web.serializers.explore import ExploreResponseSerializer
from api.rest.web.serializers.playlist import PlayListModelSerializer

from apps.category.models import Category

CACHE_TTL = 30  # seconds; tune per your needs

class ExploreAPIView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ExploreResponseSerializer

    def _build_payload(self, request):
        user = request.user if request.user.is_authenticated else None
        context = self.get_serializer_context()

        trending = trending_episodes(limit=12)
        podcasts = trending_podcasts(limit=12)
        new_releases_qs = new_releases(limit=12)
        editor = editor_picked_episodes(limit=12)
        playlists = top_playlists(limit=12)
        personalized = personalized_recommendations(user, limit=12)

        return {
            'trending': EpisodeListSerializer(trending, many=True, context=context).data,
            'new_releases': EpisodeListSerializer(new_releases_qs, many=True, context=context).data,
            'editor_picks': EpisodeListSerializer(editor, many=True, context=context).data,
            'top_playlists': PlayListModelSerializer(playlists, many=True, context=context).data,
            'recommended': EpisodeListSerializer(personalized, many=True, context=context).data,
            'categories': CategorySerializer(Category.objects.all().order_by("?")[:8], many=True, context=context).data,
            'podcasts': PodcastListSerializer(podcasts, many=True, context=context).data,
        }

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response(self._build_payload(request))

        cache_key = "web:explore:anonymous"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        data = self._build_payload(request)
        cache.set(cache_key, data, CACHE_TTL)
        return Response(data)

