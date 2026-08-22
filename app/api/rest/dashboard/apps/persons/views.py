from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework import status, viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from api.rest.exceptions import ValidationError
from apps.persons.models import Player, Fitness, Injury, InjuryType
from apps.persons.models import (
    Staff,
)
from .serializers import (
    PlayerSerializer,
    FitnessSerializer,
    InjurySerializer,
    InjuryTypeSerializer,
    PlayerModelSerializer,
    PlayerTransferSerializer,
    StaffSerializer
)


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.select_related("team", "region").prefetch_related(
        "fitness__injuries",
        "positions_played__position__shape__style",
        "goals",
        "assists"
    ).all()
    serializer_class = PlayerSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ["name", "nickname", "team__name"]
    ordering_fields = ["name", "age", "created"]
    
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method in ("post", "put", "patch"):
            return PlayerSerializer
        return PlayerModelSerializer

    # ------------------------------------------------------------
    # InjuryType - global resource (non-detail)
    # ------------------------------------------------------------
    @extend_schema(
        summary="List or create injury types",
        description="List all InjuryType or create a new global injury type (e.g. 'Hamstring').",
        responses={
            200: OpenApiResponse(response=InjuryTypeSerializer(many=True)),
            201: OpenApiResponse(response=InjuryTypeSerializer),
        },
        methods=["GET", "POST"]
    )
    @action(
        detail=False,
        methods=["get", "post"],
        url_path="injury-types",
        throttle_classes=[ScopedRateThrottle],
        # throttle_scope="injury_types",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def injury_types(self, request):
        if request.method == "GET":
            qs = InjuryType.objects.all()
            page = self.paginate_queryset(qs)
            serializer = InjuryTypeSerializer(page or qs, many=True)
            return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

        serializer = InjuryTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(InjuryTypeSerializer(obj).data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------
    # Fitness endpoints (per-player)
    # ------------------------------------------------------------
    @extend_schema(
        summary="Retrieve or modify player's fitness record",
        description=(
                "GET returns the player's Fitness (and its injury_records). "
                "POST creates a Fitness for the player (optionally with injuries). "
                "PUT/PATCH updates the Fitness: pass `injuries` (list of dicts) to replace or `injury_ids` to append."
        ),
        responses={
            200: OpenApiResponse(response=FitnessSerializer),
            201: OpenApiResponse(response=FitnessSerializer),
            404: OpenApiResponse(description="No fitness record"),
        },
        methods=["GET", "POST", "PUT", "PATCH"],
    )
    @action(
        detail=True,
        methods=["get", "post", "put", "patch"],
        url_path="fitness",
        throttle_classes=[ScopedRateThrottle],
        # throttle_scope="player_fitness_write",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def fitness(self, request, pk=None):
        player = self.get_object()

        if request.method == "GET":
            fitness = getattr(player, "fitness", None)
            if not fitness:
                return Response({"detail": "No fitness record"}, status=status.HTTP_404_NOT_FOUND)
            return Response(FitnessSerializer(fitness).data)

        # write actions require authentication
        if not request.user or not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        if request.method == "POST":
            if hasattr(player, "fitness"):
                return Response({"detail": "Fitness already exists"}, status=status.HTTP_400_BAD_REQUEST)
            payload = request.data.copy()
            payload["player"] = player.id
            serializer = FitnessSerializer(data=payload)
            serializer.is_valid(raise_exception=True)
            fitness = serializer.save()
            return Response(FitnessSerializer(fitness).data, status=status.HTTP_201_CREATED)

        # PUT / PATCH -> create if absent, otherwise update
        payload = request.data.copy()
        fitness = getattr(player, "fitness", None)
        if not fitness:
            payload["player"] = player.id
            serializer = FitnessSerializer(data=payload)
            serializer.is_valid(raise_exception=True)
            fitness = serializer.save()
            return Response(FitnessSerializer(fitness).data, status=status.HTTP_201_CREATED)

        serializer = FitnessSerializer(fitness, data=payload, partial=(request.method == "PATCH"))
        serializer.is_valid(raise_exception=True)
        fitness = serializer.save()
        return Response(FitnessSerializer(fitness).data)

    # ------------------------------------------------------------
    # Injuries (list/create for a player)
    # ------------------------------------------------------------
    @extend_schema(
        summary="List or create injuries for a player",
        description=(
                "GET: list injuries on player's fitness (paginated). "
                "POST: create one or more injury records and attach them to the player's fitness. "
                "POST accepts either a single object or a list of objects. Example item: "
                "`{ 'start_date': '2025-06-01', 'return_date': '2025-07-01', 'injury': '<injury_type_id>' }`."
        ),
        responses={
            200: OpenApiResponse(response=InjurySerializer(many=True)),
            201: OpenApiResponse(response=InjurySerializer(many=True)),
        },
        methods=["GET", "POST"],
    )
    @action(
        detail=True,
        methods=["get", "post"],
        url_path="injuries",
        throttle_classes=[ScopedRateThrottle],
        # throttle_scope="player_injuries_read",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def injuries(self, request, pk=None):
        player = self.get_object()
        fitness = getattr(player, "fitness", None)

        if request.method == "GET":
            if not fitness:
                return Response([], status=status.HTTP_200_OK)
            qs = fitness.injuries.all()
            page = self.paginate_queryset(qs)
            ser = InjurySerializer(page or qs, many=True)
            return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

        # POST -> create one or many
        if not request.user or not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        payload = request.data
        created = []
        with transaction.atomic():
            if not fitness:
                fitness = Fitness.objects.create(player=player)

            # Accept list or single object
            if isinstance(payload, list):
                for item in payload:
                    ser = InjurySerializer(data=item)
                    ser.is_valid(raise_exception=True)
                    inj = ser.save()
                    fitness.injuries.add(inj)
                    created.append(inj)
            else:
                ser = InjurySerializer(data=payload)
                ser.is_valid(raise_exception=True)
                inj = ser.save()
                fitness.injuries.add(inj)
                created.append(inj)

        out = InjurySerializer(created, many=True)
        return Response(out.data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------
    # Injury detail (per-player)
    # ------------------------------------------------------------
    @extend_schema(
        summary="Retrieve, update or delete an injury for a player",
        description="Operate on a specific injury that belongs to the player's fitness.",
        parameters=[
            OpenApiParameter(name="injury_pk", description="UUID/PK of the Injury", required=True),
        ],
        responses={
            200: OpenApiResponse(response=InjurySerializer),
            204: OpenApiResponse(description="Deleted"),
            400: OpenApiResponse(description="Bad request / wrong ownership"),
            404: OpenApiResponse(description="Not found"),
        },
        methods=["GET", "PUT", "PATCH", "DELETE"],
    )
    @action(
        detail=True,
        methods=["get", "put", "patch", "delete"],
        url_path=r"injuries/(?P<injury_pk>[^/.]+)",
        throttle_classes=[ScopedRateThrottle],
        # throttle_scope="player_injuries_write",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def injury_detail(self, request, pk=None, injury_pk=None):
        player = self.get_object()
        fitness = getattr(player, "fitness", None)
        if not fitness:
            return Response({"detail": "No fitness record for player"}, status=status.HTTP_404_NOT_FOUND)

        injury = get_object_or_404(Injury, pk=injury_pk)
        if not fitness.injuries.filter(pk=injury.pk).exists():
            return Response({"detail": "Injury does not belong to this player"}, status=status.HTTP_400_BAD_REQUEST)

        if request.method == "GET":
            return Response(InjurySerializer(injury).data)

        if request.method in ("PUT", "PATCH"):
            if not request.user or not request.user.is_authenticated:
                return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            serializer = InjurySerializer(injury, data=request.data, partial=(request.method == "PATCH"))
            serializer.is_valid(raise_exception=True)
            injury = serializer.save()
            return Response(InjurySerializer(injury).data)

        # DELETE
        if request.method == "DELETE":
            if not request.user or not request.user.is_authenticated:
                return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            with transaction.atomic():
                fitness.injuries.remove(injury)
                injury.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    # ------------------------------------------------------------
    # Transfers (per-player)
    # ------------------------------------------------------------
    @extend_schema(
        summary="List or record transfer for a player",
        description=(
                "GET: list all transfer records for a player (paginated). "
                "POST: record a transfer move for a player. "
                "POST accepts either a single object or a list of objects. Example item: "
                "`{ 'start_date': '2025-06-01', 'return_date': '2025-07-01', 'injury': '<injury_type_id>' }`."
        ),
        responses={
            200: OpenApiResponse(response=PlayerTransferSerializer(many=True)),
            201: OpenApiResponse(response=PlayerTransferSerializer(many=True)),
        },
        methods=["GET", "POST"],
    )
    @action(
        detail=True,
        methods=["get", "post"],
        url_path="transfers",
        throttle_classes=[ScopedRateThrottle],
        # throttle_scope="player_injuries_write",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def transfers(self, request, pk=None):
        player = self.get_object()

        if request.method == "GET":
            qs = player.get_transfers()
            page = self.paginate_queryset(qs)
            serializer = PlayerTransferSerializer(page or qs, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data, status=status.HTTP_200_OK)

        with transaction.atomic():
            serializer = PlayerTransferSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            date = serializer.validated_data["date"]
            for transfer in player.get_transfers():
                if not transfer.date > date:
                    raise ValidationError("Transfer of the same date cannot be recorded for a player")
            serializer.save(player=player)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        summary="Retrieve or delete a player contract info",
        description="Operate on a specific Contract related to the player's transfer.",
        parameters=[
            OpenApiParameter(name="transfer_pk", description="UUID/PK of the Transfer", required=True),
        ],
        responses={
            200: OpenApiResponse(response=PlayerTransferSerializer),
            204: OpenApiResponse(description="Deleted"),
            400: OpenApiResponse(description="Bad request / wrong ownership"),
            404: OpenApiResponse(description="Not found"),
        },
        methods=["GET", "PUT", "PATCH", "DELETE"],
    )
    @action(
        detail=True,
        methods=["get", "delete"],
        url_path=r"transfer/(?P<transfer_pk>[^/.]+)",
        throttle_classes=[ScopedRateThrottle],
        # throttle_scope="player_injuries_write",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def contract(self, request, pk=None, transfer_pk=None):
        player = self.get_object()

        transfer = player.get_transfers().filter(pk=transfer_pk)

        if request.method == "DELETE":
            if not request.user or not request.user.is_authenticated:
                raise PermissionDenied({"detail": "Authentication required"})
            if not request.user.is_staff:
                raise PermissionDenied({"detail": "You do not have permission to perform this action"})
            with transaction.atomic():
                transfer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(PlayerTransferSerializer(transfer).data)


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.select_related("team", "region").all()
    serializer_class = StaffSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name", "job"]
