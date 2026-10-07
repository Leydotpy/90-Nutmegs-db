"""Composite serializers for the public Explore feed."""

from rest_framework import serializers

from api.rest.web.apps.podcasts.serializers import (
    EpisodeListSerializer,
    PodcastListSerializer,
)
from api.rest.web.serializers.category import CategorySerializer
from api.rest.web.serializers.playlist import PlayListModelSerializer


class ExploreResponseSerializer(serializers.Serializer):
    """Bounded rail contract returned by the public Explore endpoint."""

    trending = EpisodeListSerializer(many=True, read_only=True)
    new_releases = EpisodeListSerializer(many=True, read_only=True)
    editor_picks = EpisodeListSerializer(many=True, read_only=True)
    top_playlists = PlayListModelSerializer(many=True, read_only=True)
    recommended = EpisodeListSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    podcasts = PodcastListSerializer(many=True, read_only=True)
