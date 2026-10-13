from api.rest.dashboard.audit import StaffAuditMixin
from api.rest.dashboard.permissions import ActiveStaff
# ------------------------
# ViewSets
# ------------------------
from apps.media.audio.models import Audio
from apps.media.images.models import Image
from apps.posts.podcasts.models import Episode, Podcast, Season
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from api.rest.dashboard.apps.media.audio.serializers import AudioSerializer
from api.rest.dashboard.apps.media.images.serializers import (
    ImageSerializer,
    _create_image_for_instance,
)

from .serializers import (
    EpisodeModelSerializer,
    EpisodeSerializer,
    PodcastModelSerializer,
    PodcastSerializer,
    SeasonSerializer,
)


class PodcastViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    """
    ViewSet for Podcast. Supports listing, creating, updating Podcasts and
    prefetches analytics M2M for performance.
    """
    permission_classes = [ActiveStaff]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ["title", "subtitle", "tags", "category__title"]
    ordering_fields = ["title", "timestamp"]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return PodcastModelSerializer
        return PodcastSerializer

    def get_queryset(self):
        return Podcast.objects.prefetch_related(
            "categories",
            "episodes",
            "seasons",
            "countries",
            "competitions",
            "regions",
            "teams",
            "players",
            "matches",
            "subscribers",
        ).all()

    @action(
        methods=["get"],
        detail=True,
        url_path="episodes",
        throttle_classes=[ScopedRateThrottle],
    )
    def episodes(self, request, pk=None):
        podcast = self.get_object()
        qs = podcast.get_episodes()
        filtered = self.filter_queryset(qs)
        page = self.paginate_queryset(filtered)
        serializer = EpisodeModelSerializer(
            page or filtered,
            many=True,
            context={"request": request},
        )
        return (
            self.get_paginated_response(serializer.data)
            if page is not None
            else Response(serializer.data, status=status.HTTP_200_OK)
        )

    @extend_schema(
        operation_id="dashboard_podcast_seasons_list",
        responses=SeasonSerializer(many=True),
    )
    @action(
        methods=["get"],
        detail=True,
        url_path="seasons",
        throttle_classes=[ScopedRateThrottle],
    )
    def seasons(self, request, pk=None):
        podcast = self.get_object()
        seasons = podcast.get_seasons()
        page = self.paginate_queryset(seasons)
        serializer = SeasonSerializer(page or seasons, many=True, context={"request": request})
        return (
            self.get_paginated_response(serializer.data)
            if page is not None
            else Response(serializer.data, status=status.HTTP_200_OK)
        )


    # @action(
    #     methods=["get"],
    #     detail=True,
    #     url_path="episodes/(?P<episode_id>[^/.]+)>)"
    # )
    # def episode(self, request, pk=None, episode_id=None):
    #     podcast = self.get_object()
    #     episode = get_object_or_404(podcast.get_episodes(), pk=episode_id)
    #     return EpisodeModelSerializer(episode, context={"request": request}).data

    @action(
        detail=True,
        methods=["post"],
        url_path="images",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_image(self, request, pk=None):
        """
        Upload a single image file for this podcast.
        Accepts multipart/form-data with 'file' and optional 'title'.
        """
        instance = self.get_object()
        file_obj = request.FILES.get("file")
        title = request.data.get("title", None)

        if not file_obj:
            return Response({"detail": "file is required"}, status=status.HTTP_400_BAD_REQUEST)

        img_data = {"file": file_obj, "title": title}
        try:
            with transaction.atomic():
                img = _create_image_for_instance(instance, img_data)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ImageSerializer(img, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"images/(?P<image_id>[^/.]+)")
    def delete_image(self, request, pk=None, image_id=None):
        """
        Delete an image by image id from this podcast.
        """
        instance = self.get_object()
        # find image
        try:
            img = Image.objects.get(pk=image_id)
        except Image.DoesNotExist:
            return Response({"detail": "image not found"}, status=status.HTTP_404_NOT_FOUND)

        ct = ContentType.objects.get_for_model(instance.__class__)

        # validate ownership
        if img.content_type != ct or str(img.object_id) != str(instance.pk):
            # again, if your instance.pk is UUID and image.object_id is integer this will mismatch.
            return Response(
                {"detail": "image does not belong to this resource"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # safe deletion
        img.delete()
        return Response({"detail": "image deleted"}, status=status.HTTP_204_NO_CONTENT)


class SeasonViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    permission_classes = [ActiveStaff]
    serializer_class = SeasonSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ["title", "description", "slug", "podcast__title"]
    ordering_fields = ["position", "number", "published_at", "created_at"]
    filterset_fields = ["podcast"]

    def get_queryset(self):
        return Season.objects.select_related("podcast", "legacy_podcast").all()


class EpisodeViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    permission_classes = [ActiveStaff]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["title", "subtitle", "tags", "hosts"]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return EpisodeModelSerializer
        return EpisodeSerializer

    def get_queryset(self):
        return Episode.objects.select_related("podcast", "season").prefetch_related(
            "categories", "countries", "competitions", "regions", "teams", "players", "matches"
        ).all()

    @action(
        detail=True,
        methods=["post"],
        url_path="images",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_image(self, request, pk=None):
        """
        Upload a single image file for this podcast.
        Accepts multipart/form-data with 'file' and optional 'title'.
        """
        instance = self.get_object()
        file_obj = request.FILES.get("file")
        title = request.data.get("title", None)

        if not file_obj:
            return Response({"detail": "file is required"}, status=status.HTTP_400_BAD_REQUEST)

        img_data = {"file": file_obj, "title": title}
        try:
            with transaction.atomic():
                img = _create_image_for_instance(instance, img_data)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ImageSerializer(img, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"images/(?P<image_id>[^/.]+)")
    def delete_image(self, request, pk=None, image_id=None):
        """
        Delete an image by image id from this podcast.
        """
        instance = self.get_object()
        # find image
        try:
            img = Image.objects.get(pk=image_id)
        except Image.DoesNotExist:
            return Response({"detail": "image not found"}, status=status.HTTP_404_NOT_FOUND)

        ct = ContentType.objects.get_for_model(instance.__class__)

        # validate ownership
        if img.content_type != ct or str(img.object_id) != str(instance.pk):
            # again, if your instance.pk is UUID and image.object_id is integer this will mismatch.
            return Response(
                {"detail": "image does not belong to this resource"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # safe deletion
        img.delete()
        return Response({"detail": "image deleted"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def audios(self, request, pk=None):
        episode = self.get_object()
        serializer = AudioSerializer(episode.audios.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def upload_audio(self, request, pk=None):
        episode = self.get_object()

        serializer = AudioSerializer(
            data=request.data,
            context={"episode": episode}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="audio/(?P<audio_id>[^/.]+)")
    def update_audio(self, request, pk=None, audio_id=None):
        episode = self.get_object()

        try:
            audio = episode.audios.get(pk=audio_id)
        except Audio.DoesNotExist:
            return Response({"detail": "Audio not found"}, status=404)

        serializer = AudioSerializer(
            audio,
            data=request.data,
            partial=True,
            context={"episode": episode}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(detail=True, methods=["delete"], url_path="audio/(?P<audio_id>[^/.]+)")
    def delete_audio(self, request, pk=None, audio_id=None):
        episode = self.get_object()

        try:
            audio = episode.audios.get(pk=audio_id)
        except Audio.DoesNotExist:
            return Response({"detail": "Audio not found"}, status=404)

        audio.file.delete(save=False)
        audio.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
