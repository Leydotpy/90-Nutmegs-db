from apps.accounts.history import UserHistoryManager
from apps.posts.podcasts.models import Episode, PlayBack, Podcast
from apps.posts.podcasts.signals import podcast_viewed
from apps.promotions.models import AutomaticPostList, HandPickedPostList
from apps.promotions.models import Image as PromotionImage
from rest_framework import filters
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    get_object_or_404,
)
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.rest.dashboard.pagination import StandardResultPagination
from api.rest.web.apps.podcasts.serializers import (
    AutomaticPodcastPromotionSerializer,
    EpisodeDetailSerializer,
    EpisodeListSerializer,
    HandPickedPodcastPromotionSerializers,
    ImageBannerPromotionSerializer,
    PlayBackModelSerializer,
    PlayBackUpdateSerializer,
    PodcastDetailSerializer,
    PodcastListSerializer,
    PromotionSerializer,
)
from api.rest.web.apps.podcasts.utils import make_automatic_post_module, make_handpicked_module
from api.rest.web.serializers.comments import CommentDetailSerializer
from api.rest.web.utils import PageNumberPaginationClass


class TrendingPodcastAPIView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = PodcastListSerializer
    pagination_class = PageNumberPaginationClass

    def get_queryset(self):
        return Podcast.objects.trending()


# Import your serializers and models here


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


class PodcastDetailAPIView(RetrieveAPIView):
    queryset = Podcast.objects.all()
    serializer_class = PodcastDetailSerializer
    permission_classes = (AllowAny,)
    lookup_field = "slug"

    def get_queryset(self):
        # Resolve the publication window at request time, not module import time.
        return Podcast.objects.published()

    def get_episodes_queryset(self, podcast):
        """
        Determines which episodes to show based on query params.
        Logic: If 'season' param exists, fetch that season's episodes.
        Otherwise, fetch the podcast's direct episodes.
        """
        season_slug = self.request.query_params.get("season")

        if season_slug:
            # Resolve the explicit canonical Season by its stable slug.
            season = podcast.get_seasons().published().filter(slug=season_slug).first()
            if season:
                return season.get_discoverable_episodes().select_related("season")

        # Fallback: Return direct episodes of the podcast
        # Or if you want the first season's episodes by default:
        first_season = podcast.get_seasons().published().first()
        if first_season:
            return first_season.get_discoverable_episodes().select_related("season")

        return podcast.get_discoverable_episodes().select_related("season")

    def retrieve(self, request, *args, **kwargs):
        """
        Overridden retrieve to handle manual pagination of the nested 'episodes' list.
        """

        podcast = self.get_object()

        # Record viewing of this podcast for analytical purposes

        podcast.record_view(request)

        # 1. Get the episodes intended for display
        episodes_qs = self.get_episodes_queryset(podcast)

        # 2. Paginate the episodes
        paginator = StandardResultsSetPagination()
        paginated_episodes = paginator.paginate_queryset(episodes_qs, request)

        # 3. Serialize the episodes separately
        episodes_data = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": EpisodeListSerializer(
                paginated_episodes, many=True, context={"request": request}
            ).data,
        }

        # 4. Pass the episode data to the main serializer context
        serializer = self.get_serializer(
            podcast, context={"request": request, "paginated_episodes": episodes_data}
        )

        response = Response(serializer.data)

        podcast_viewed.send(
            sender=self, request=request, podcast=podcast, response=response, user=request.user
        )
        return response


class RecentlyViewedPodcastAPIView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = PodcastListSerializer

    def get_queryset(self):
        return UserHistoryManager.get(self.request)


class EpisodeDetailAPIView(RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = EpisodeDetailSerializer
    lookup_field = "slug"
    queryset = Episode.objects.all()

    def get_queryset(self):
        return Episode.objects.discoverable().select_related("podcast", "season")


class EpisodeListAPIView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = EpisodeListSerializer
    lookup_field = "slug"
    pagination_class = PageNumberPaginationClass

    def get_object(self) -> Podcast:
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        return get_object_or_404(Podcast.objects.published(), **filter_kwargs)

    def get_queryset(self):
        return self.get_object().get_discoverable_episodes().select_related("season")


class HandpickedPromotionsAPIView(ListAPIView):
    serializer_class = HandPickedPodcastPromotionSerializers
    queryset = HandPickedPostList.objects.order_by("pk")
    permission_classes = (AllowAny,)


class AutomaticPromotionAPIView(ListAPIView):
    serializer_class = AutomaticPodcastPromotionSerializer
    queryset = AutomaticPostList.objects.order_by("pk")
    permission_classes = (AllowAny,)


class PromotionsAPIView(GenericAPIView):
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        return PromotionSerializer

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("context", self.get_serializer_context())
        return self.get_serializer_class()(*args, **kwargs)

    def make_module(self, instance):
        serializer = self.get_serializer(instance, many=True)
        return serializer.data

    def get(self, request, *args, **kwargs):
        automatic = make_automatic_post_module(self)
        handpicked = make_handpicked_module(self)
        promotions = {
            "automatic": self.make_module(automatic),
            "handpicked": self.make_module(handpicked),
            "banners": ImageBannerPromotionSerializer(
                PromotionImage.objects.ready().discoverable(),
                many=True,
                context=self.get_serializer_context(),
            ).data,
        }
        history = PodcastListSerializer(
            UserHistoryManager.get(request), many=True, context=self.get_serializer_context()
        ).data
        trending = PodcastListSerializer(
            Podcast.objects.trending(), many=True, context=self.get_serializer_context()
        ).data
        playback = PlayBackModelSerializer(
            PlayBack.objects.get_uncompleted(request),
            many=True,
            context=self.get_serializer_context(),
        ).data
        data = {
            "promotions": promotions,
            "history": history,
            "trending": trending,
            "playback": playback,
        }
        return Response(data)


class PlayBackListApiView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PlayBackModelSerializer
    pagination_class = CursorPagination

    def get_queryset(self):
        return PlayBack.objects.get_recently_played(request=self.request)


class PlaybackUncompletedListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PlayBackModelSerializer

    def get_queryset(self):
        return PlayBack.objects.get_uncompleted(request=self.request)


class PlaybackUpdateAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PlayBackUpdateSerializer
    queryset = Episode.objects.all()
    lookup_field = "slug"

    def get_queryset(self):
        return Episode.objects.discoverable()

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class PodcastCommentListAPIView(ListAPIView):
    serializer_class = CommentDetailSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["content", "user__username", "user__first_name", "user__last_name"]
    lookup_url_kwarg = "podcast_id"
    lookup_field = "id"

    def get_queryset(self):
        podcast = get_object_or_404(
            Podcast.objects.published(),
            pk=self.kwargs[self.lookup_url_kwarg],
        )
        return podcast.get_comments().select_related("user")
