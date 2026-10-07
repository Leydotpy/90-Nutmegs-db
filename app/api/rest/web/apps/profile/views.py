from apps.media.models import MediaSettings, PlayList, PlaylistItem
from apps.posts.podcasts.models import Episode, Podcast
from django.db import models, transaction
from rest_framework import parsers, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response

from api.rest.web.apps.podcasts.serializers import (
    PodcastListSerializer,
    SubscribeSerializer,
)
from api.rest.web.serializers.media import MediaSettingModelSerializer
from api.rest.web.serializers.playlist import (
    PlayListModelSerializer,
    PlaylistUserCreateSerializer,
)
from api.rest.web.utils import PageNumberPaginationClass


class IsOwnerOrReadOnly(BasePermission):
    """
    Allow safe methods for everyone. For unsafe methods only allow if the request.user
    is the playlist owner (based on profiles.Profile on request.user.profile).
    If playlist.user is None (public / system playlist) editing is denied.
    Adjust get_profile_from_user if your User->Profile relation differs.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Deny if playlist has no owner (system playlists are not editable by arbitrary users)
        if obj.user is None:
            return False
        return request.user.is_authenticated and obj.user == request.user


class PlaylistUserViewSet(viewsets.ModelViewSet):
    serializer_class = PlaylistUserCreateSerializer
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPaginationClass
    filter_backends = (OrderingFilter, SearchFilter)
    search_fields = ('name', 'items__title', 'timestamp', 'items__podcast__name', 'items__timestamp')

    """
       CRUD + helper actions for Playlists.

       - Supports multipart/form-data uploads via the `file` write-only field on the serializer.
       - Custom actions:
         * POST /playlists/{pk}/add_item/   { "episode_id": 1, "position": 3 }
         * POST /playlists/{pk}/remove_item/ { "episode_id": 1 }
         * POST /playlists/{pk}/reorder/    { "order": [3, 5, 1] }  # episode ids in desired order
       """

    def get_permissions(self):
        # read-only endpoints are open, modifications require authentication and ownership.
        if self.action in ("create", "update", "partial_update", "destroy", "add_item", "remove_item", "reorder"):
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # keep update atomic if serializer touches files + relations
        with transaction.atomic():
            playlist = serializer.save()
            if not playlist.user:
                playlist.user = self.request.user
                playlist.save(update_fields=["user"])

    def get_queryset(self):
        return PlayList.objects.for_user(user=self.request.user).select_related(
            "image", "user").prefetch_related("items", "categories")

    @action(detail=True, methods=["get"], url_path="view_item")
    def view_item(self, request, pk=None):
        instance = self.get_object()
        ser = PlayListModelSerializer(instance)
        return Response(ser.data)

    @action(detail=True, methods=["post"], url_path="reorder")
    def reorder(self, request, pk=None):
        """
        Accepts JSON: {"order": [episode_id1, episode_id2, ...]}
        Sets position=0..N-1 according to list order for items that exist in the playlist.
        """
        playlist = self.get_object()
        self.check_object_permissions(request, playlist)

        order = request.data.get("order")
        if not isinstance(order, (list, tuple)):
            return Response({"detail": "order must be a list of episode ids"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Build map for quick lookup then update positions in one pass
            existing_items = {pi.episode_id: pi for pi in PlaylistItem.objects.filter(playlist=playlist)}
            updated = []
            for pos, ep_id in enumerate(order):
                if ep_id in existing_items:
                    pi = existing_items[ep_id]
                    if pi.position != pos:
                        pi.position = pos
                        pi.save(update_fields=["position"])
                    updated.append(ep_id)

        return Response({"detail": "reordered", "updated": updated}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="add_item")
    def add_item(self, request, pk=None):
        """
        Add one or many episodes to a playlist.

        Accepts:
          - single: { "episode_id": 1, "position": 3 }  (position optional)
          - batch:  { "items": [ { "episode_id": 1, "position": 0 }, { "episode_id": 2 } ] }

        Behavior:
          - If an item already exists it is updated (position updated if provided).
          - If position is omitted, new items are appended after the current max position.
        """
        playlist = self.get_object()
        self.check_object_permissions(request, playlist)

        # Normalize input into list of dicts: [{"episode_id": .., "position": ..}, ...]
        raw_items = request.data.get("items")
        if raw_items is None:
            # support single item short-form
            ep = request.data.get("episode_id")
            if ep is None:
                return Response({"detail": "episode_id or items is required"}, status=status.HTTP_400_BAD_REQUEST)
            raw_items = [{"episode_id": ep, "position": request.data.get("position")}]

        if not isinstance(raw_items, (list, tuple)):
            return Response({"detail": "items must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate and collect episode IDs
        try:
            parsed = []
            for it in raw_items:
                if not isinstance(it, dict):
                    raise ValueError("each item must be an object with 'episode_id' and optional 'position'")
                ep_id = it.get("episode_id")
                if ep_id is None:
                    raise ValueError("each item must include 'episode_id'")
                position = it.get("position")
                if position is not None:
                    position = int(position)  # may raise
                parsed.append({"episode_id": int(ep_id), "position": position})
        except (ValueError, TypeError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        episode_ids = [p["episode_id"] for p in parsed]
        episodes = {e.pk: e for e in Episode.objects.discoverable().filter(pk__in=episode_ids)}
        missing = [eid for eid in episode_ids if eid not in episodes]
        if missing:
            return Response({"detail": "some episodes not found", "missing": missing}, status=status.HTTP_404_NOT_FOUND)

        # Preload existing PlaylistItems for this playlist
        existing_items_qs = PlaylistItem.objects.filter(playlist=playlist, episode_id__in=episode_ids)
        existing_map = {pi.episode_id: pi for pi in existing_items_qs}

        # Find current max position to append new items if needed
        max_pos = PlaylistItem.objects.filter(playlist=playlist).aggregate(
            max_pos=models.Max("position")
        )["max_pos"]
        if max_pos is None:
            max_pos = -1

        created = []
        updated = []
        errors = []

        with transaction.atomic():
            next_append_pos = max_pos + 1
            for p in parsed:
                eid = p["episode_id"]
                pos = p["position"]
                if eid in existing_map:
                    pi = existing_map[eid]
                    if pos is not None and pi.position != pos:
                        pi.position = pos
                        pi.save(update_fields=["position"])
                        updated.append({"episode_id": eid, "position": pos})
                    else:
                        # nothing to change
                        updated.append({"episode_id": eid, "position": pi.position})
                else:
                    assign_pos = pos if pos is not None else next_append_pos
                    try:
                        pi = PlaylistItem.objects.create(playlist=playlist, episode=episodes[eid], position=assign_pos)
                        created.append({"episode_id": eid, "position": assign_pos})
                        if pos is None:
                            next_append_pos += 1
                    except Exception as exc:
                        errors.append({"episode_id": eid, "error": str(exc)})

        resp = {"created": created, "updated": updated}
        if errors:
            resp["errors"] = errors
            return Response(resp, status=status.HTTP_207_MULTI_STATUS)  # partial success
        return Response(resp, status=status.HTTP_200_OK if updated and not created else status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="remove_item")
    def remove_item(self, request, pk=None):
        """
        Remove one or many episodes from a playlist.

        Accepts:
          - single: { "episode_id": 1 }
          - batch:  { "episode_ids": [1, 2, 3] }
          - batch alt: { "items": [ { "episode_id": 1 }, { "episode_id": 2 } ] }
        """
        playlist = self.get_object()
        self.check_object_permissions(request, playlist)

        # Normalize to a list of ids
        episode_ids = request.data.get("episode_ids")
        if episode_ids is None:
            raw_items = request.data.get("items")
            if raw_items is None:
                ep = request.data.get("episode_id")
                if ep is None:
                    return Response({"detail": "episode_id or episode_ids or items is required"},
                                    status=status.HTTP_400_BAD_REQUEST)
                episode_ids = [int(ep)]
            else:
                if not isinstance(raw_items, (list, tuple)):
                    return Response({"detail": "items must be a list"}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    episode_ids = [int(it["episode_id"]) for it in raw_items]
                except Exception:
                    return Response({"detail": "each item must be an object with 'episode_id'"},
                                    status=status.HTTP_400_BAD_REQUEST)
        else:
            if not isinstance(episode_ids, (list, tuple)):
                return Response({"detail": "episode_ids must be a list"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                episode_ids = [int(e) for e in episode_ids]
            except Exception:
                return Response({"detail": "episode_ids must contain integers"}, status=status.HTTP_400_BAD_REQUEST)

        if not episode_ids:
            return Response({"detail": "no episode ids provided"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            items_qs = PlaylistItem.objects.filter(playlist=playlist, episode_id__in=episode_ids)
            found_ids = list(items_qs.values_list("episode_id", flat=True))
            deleted_count, _ = items_qs.delete()

        missing = [eid for eid in episode_ids if eid not in found_ids]
        resp = {"removed": found_ids, "count": deleted_count}
        if missing:
            resp["missing"] = missing
            # still return 200 because we successfully removed the found ones
            return Response(resp, status=status.HTTP_200_OK)
        return Response(resp, status=status.HTTP_200_OK)


class FeaturedPlayListAPIView(ListAPIView):
    serializer_class = PlayListModelSerializer
    permission_classes = (AllowAny,)
    pagination_class = PageNumberPaginationClass
    filter_backends = (OrderingFilter, SearchFilter)
    search_fields = ('name', 'items__title', 'timestamp', 'items__podcast__name', 'items__timestamp')

    def get_queryset(self):
        return PlayList.objects.featured()


class UserSubscriptionAPIView(CreateModelMixin, GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        return SubscribeSerializer

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


# class ReactToModelAPIView(GenericAPIView, CreateModelMixin, UpdateModelMixin, DestroyModelMixin):
#     permission_classes = (IsAuthenticated,)
#     lookup_field = "id"
#
#     def get_queryset(self):
#         return PostReaction.objects.all()
#
#     def get_serializer(self, *args, **kwargs):
#         serializer_klass = ReactionCreateSerializer
#         kwargs.setdefault("context", self.get_serializer_context())
#         return serializer_klass(*args, **kwargs)
#
#     def get_object(self):
#         if self.kwargs.get("id"):
#             return super().get_object()
#         raise RuntimeError(f"Attempt to call {self.__class__.__name__} through the wrong url."
#                            f"make sure you call the view directly through a url that specify a lookup field")
#
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         headers = self.get_success_headers(serializer.data)
#         reaction = PostReactionSerializer(serializer.instance).data
#         return Response(reaction, status=status.HTTP_201_CREATED, headers=headers)


class ReactionsListApiView(RetrieveAPIView):
    ...


class SubscribedListPodcastAPIView(ListAPIView):
    serializer_class = PodcastListSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPaginationClass

    def get_queryset(self):
        return Podcast.objects.get_user_subscriptions(self.request.user)


class MediaSettingsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _get_or_create_settings(self, user):
        settings_obj, created = MediaSettings.objects.get_or_create(user=user)
        return settings_obj

    def retrieve(self, request):
        """GET /api/media-settings/  -> returns the current user's settings"""
        obj = self._get_or_create_settings(request.user)
        serializer = MediaSettingModelSerializer(obj)
        return Response(serializer.data)

    def partial_update(self, request):
        """PATCH /api/media-settings/  -> partial update

        Accepts any subset of serializer fields.
        """
        obj = self._get_or_create_settings(request.user)
        serializer = MediaSettingModelSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def update(self, request):
        """PUT /api/media-settings/  -> replace (you might prefer PATCH only)
        """
        obj = self._get_or_create_settings(request.user)
        serializer = MediaSettingModelSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # Optional: reset to defaults
    def destroy(self, request):
        """DELETE /api/media-settings/ -> reset to defaults (or delete user's settings)
        """
        obj = self._get_or_create_settings(request.user)
        # Decide behaviour: either reset fields to defaults or delete the row
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
