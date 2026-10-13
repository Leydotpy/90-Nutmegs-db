from api.rest.dashboard.audit import StaffAuditMixin
from api.rest.dashboard.permissions import ActiveStaff
from django.db import transaction
from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import permissions, filters
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# import the serializers defined above
from api.rest.dashboard.apps.tactics.serializers import (
    MatchLineUpSerializer,
    TeamLineUpCreateSerializer,
)
from api.rest.pagination import StandardPagination
from api.rest.throttling import BurstUserThrottle, SustainedUserThrottle, AnonymousBurstThrottle
from apps.match.models import Match, GoalEvent, FoulEvent
from apps.tactics.models import TeamLineUp as TeamLineUpModel, MatchLineUp as MatchLineUpModel
from .serializers import (
    ShotCreateSerializer, GoalCreateSerializer, FoulCreateSerializer,
    SetPieceCreateSerializer, BookingCreateSerializer, SubstitutionCreateSerializer,
    TimelineItemSerializer, MatchSerializer
)
from ..region.serializers import TeamModelSerializer


def minute_from_timefield(timefield):
    """helper: if model stores minute as TimeField, convert to integer minute"""
    try:
        return timefield.hour * 60 + timefield.minute
    except Exception:
        return None


class MatchViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    serializer_class = MatchSerializer
    permission_classes = [ActiveStaff]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["home_team", "away_team", "date", "competition", "campaign"]
    search_fields = ["home_team__name", "away_team__name"]
    ordering_fields = ["date", "day"]
    pagination_class = StandardPagination
    throttle_classes = [BurstUserThrottle, SustainedUserThrottle]

    def get_queryset(self):
        return Match.objects.select_related(
            "home_team",
            "away_team",
            "venue",
            "competition",
            "campaign").prefetch_related(
            Prefetch("event__goals"),
            Prefetch("event__shots"),
            Prefetch("event__fouls"),
            Prefetch("event__substitutions"),
        ).all()

    @method_decorator(cache_page(60))  # cache for 60s
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    # Live endpoints for creating events. Each is POST /matches/{pk}/live/<event>/
    @action(detail=True, methods=["post"], url_path="live/shot", throttle_classes=[BurstUserThrottle])
    def create_shot(self, request, pk=None):
        match = self.get_object()
        serializer = ShotCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            shot = serializer.save()
            # attach to event
            match.event.shots.add(shot)
        return Response({"detail": "shot recorded", "id": shot.id}, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=GoalCreateSerializer,
        responses={201: OpenApiResponse(description="Goal given")}
    )
    @action(detail=True, methods=["post"], url_path="live/goal", throttle_classes=[BurstUserThrottle])
    def create_goal(self, request, pk=None):
        match = self.get_object()
        serializer = GoalCreateSerializer(data=request.data, context={"match": match})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            goal = serializer.save()
            GoalEvent.objects.create(event=match.event, goal=goal)
        return Response({"detail": "goal recorded", "id": goal.id}, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=FoulCreateSerializer,
        responses={201: OpenApiResponse(description="Foul recorded")}
    )
    @action(detail=True, methods=["post"], url_path="live/foul", throttle_classes=[BurstUserThrottle])
    def create_foul(self, request, pk=None):
        match = self.get_object()
        serializer = FoulCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            foul = serializer.save()
            match.event.fouls.add(foul)
            FoulEvent.objects.create(event=match.event, foul=foul)
        return Response({"detail": "foul recorded", "id": foul.id}, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=SetPieceCreateSerializer,
        responses={201: OpenApiResponse(description="SetPiece recorded")}
    )
    @action(detail=True, methods=["post"], url_path="live/set-piece", throttle_classes=[BurstUserThrottle])
    def create_set_piece(self, request, pk=None):
        match = self.get_object()
        serializer = SetPieceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            sp = serializer.save()
            match.event.set_piece.add(sp)
        return Response({"detail": "set-piece recorded", "id": sp.id}, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=BookingCreateSerializer,
        responses={201: OpenApiResponse(description="Booking recorded")}
    )
    @action(detail=True, methods=["post"], url_path="live/booking", throttle_classes=[BurstUserThrottle])
    def create_booking(self, request, pk=None):
        match = self.get_object()
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            booking = serializer.save()
            match.event.bookings.add(booking)
        return Response({"detail": "booking recorded", "id": booking.id}, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=SubstitutionCreateSerializer,
        responses={201: OpenApiResponse(description="Substitution made")}
    )
    @action(detail=True, methods=["post"], url_path="live/substitution", throttle_classes=[BurstUserThrottle])
    def create_substitution(self, request, pk=None):
        match = self.get_object()
        serializer = SubstitutionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            sub = serializer.save()
            match.event.substitutions.add(sub)
        return Response({"detail": "substitution recorded", "id": sub.id}, status=status.HTTP_201_CREATED)

    # Timeline endpoint
    @action(detail=True, methods=["get"], url_path="timeline", throttle_classes=[AnonymousBurstThrottle])
    @method_decorator(cache_page(5))  # cache for 5 seconds for heavy traffic
    def timeline(self, request, pk=None):
        match = self.get_object()
        event = match.event  # guaranteed by signal on match create
        timeline = []

        # Goals
        goals = event.goals.select_related("scorer", "assist", "team").all()
        for g in goals:
            minute = getattr(g, "minute", None)
            m = None
            if minute is not None:
                try:
                    m = int(minute.hour * 60 + minute.minute)
                except Exception:
                    m = None
            timeline.append({
                "id": f"goal:{g.id}",
                "type": "goal",
                "minute": m,
                "team": TeamModelSerializer(g.team).data,
                "player": str(g.scorer),
                "payload": {
                    "assist": str(g.assist) if g.assist else None,
                    "is_own_goal": g.is_own_goal
                }
            })

        # Shots
        shots = event.shots.select_related("player", "team").all()
        for s in shots:
            timeline.append({
                "id": f"shot:{s.id}",
                "type": "shot",
                "minute": minute_from_timefield(s.minute),
                "team": TeamModelSerializer(s.team).data,
                "player": str(s.player),
                "payload": {"is_on_target": s.is_on_target}
            })

        # Fouls
        fouls = event.fouls.select_related("player", "team").all()
        for f in fouls:
            timeline.append({
                "id": f"foul:{f.id}",
                "type": "foul",
                "minute": minute_from_timefield(f.minute),
                "team": TeamModelSerializer(f.team).data,
                "player": str(f.player),
                "payload": {}
            })

        # Bookings
        bookings = event.bookings.select_related("player", "team").all()
        for b in bookings:
            timeline.append({
                "id": f"booking:{b.id}",
                "type": "booking",
                "minute": b.minute,
                "team": TeamModelSerializer(b.team).data,
                "player": str(b.player),
                "payload": {"booking": b.booking, "is_straight_red": b.is_straight_red}
            })

        # Substitutions
        subs = event.substitutions.select_related("player_in", "player_out", "team").all()
        for s in subs:
            timeline.append({
                "id": f"sub:{s.id}",
                "type": "substitution",
                "minute": s.minute,
                "team": str(s.team),
                "player": f"in:{s.player_in} out:{s.player_out}",
                "payload": {"reason": s.reason}
            })

        # Set pieces
        setpieces = event.set_piece.select_related("team").all()
        for sp in setpieces:
            timeline.append({
                "id": f"setpiece:{sp.id}",
                "type": "set_piece",
                "minute": minute_from_timefield(sp.minute),
                "team": TeamModelSerializer(sp.team).data,
                "player": None,
                "payload": {"type": sp.type}
            })

        # Sort timeline by minute (None values will go last). If minute ties, fall back to id.
        def sort_key(item):
            m_ = item.get("minute")
            return m_ is None, m_ if m_ is not None else 9999, item["id"]

        timeline.sort(key=sort_key)

        serializer = TimelineItemSerializer(timeline, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="lineups")
    def match_lineups(self, request, pk=None):
        """
        Create (or attach existing) home and away team lineups for this match.

        Payload example (two options):
        1) Reference existing TeamLineUp objects:
           {
             "home_lineup_data": {"id": 123},
             "away_lineup_data": {"id": 456}
           }

        2) Create nested TeamLineUp objects:
           {
             "home_lineup_data": {
               "team": <home_team_id>,
               "formation": <formation_id>,
               "manager": <staff_id>,
               "lineup": [{"player": <player_id>, "position": <position_id>}, ...]
             },
             "away_lineup_data": { ... similar ... }
           }

        Validation:
         - home_lineup.team must match match.home_team
         - away_lineup.team must match match.away_team
         - prevents creating a second MatchLineUp for a match unless you use PATCH below
        """
        match = self.get_object()

        # If a MatchLineUp already exists, reject to avoid accidental duplicate creations.
        # If you want to support replacing lineups, add a query param like ?replace=true
        if hasattr(match, "lineups"):
            # For OneToOneField, accessing related attribute either returns object or raises DoesNotExist.
            try:
                existing = match.lineups
                return Response({"detail": "Lineups already exist for this match."}, status=status.HTTP_400_BAD_REQUEST)
            except MatchLineUpModel.DoesNotExist:
                pass

        home_payload = request.data.get("home_lineup_data")
        away_payload = request.data.get("away_lineup_data")

        if not home_payload or not away_payload:
            return Response({"detail": "Both home_lineup_data and away_lineup_data are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Validate and create (or fetch) TeamLineUp for home and away
        home_serializer = TeamLineUpCreateSerializer(data=home_payload)
        away_serializer = TeamLineUpCreateSerializer(data=away_payload)
        home_serializer.is_valid(raise_exception=True)
        away_serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # create or get home_team_lineup
            home_lineup_obj = home_serializer.save() if not home_payload.get("id") else TeamLineUpModel.objects.get(
                pk=home_payload["id"])
            away_lineup_obj = away_serializer.save() if not away_payload.get("id") else TeamLineUpModel.objects.get(
                pk=away_payload["id"])

            # Validation: ensure the team ids match match.home_team / match.away_team
            if str(home_lineup_obj.team.pk) != str(match.home_team.pk):
                return Response({"detail": "home_lineup team does not match match.home_team"},
                                status=status.HTTP_400_BAD_REQUEST)
            if str(away_lineup_obj.team.pk) != str(match.away_team.pk):
                return Response({"detail": "away_lineup team does not match match.away_team"},
                                status=status.HTTP_400_BAD_REQUEST)

            # create MatchLineUp linking them
            match_lineup = MatchLineUpModel.objects.create(
                match=match,
                home_lineup=home_lineup_obj,
                away_lineup=away_lineup_obj
            )

            # Serialize the created MatchLineUp for response
            out = MatchLineUpSerializer(match_lineup, context={"request": request})
            return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="lineups")
    def update_lineups(self, request, pk=None):
        match = self.get_object()
        try:
            match_lineup = match.lineups
        except MatchLineUpModel.DoesNotExist:
            return Response({"detail": "No existing lineups found"}, status=status.HTTP_404_NOT_FOUND)

        # Accept partial nested updates: allow client to pass updated home_lineup_data or away_lineup_data
        home_payload = request.data.get("home_lineup_data")
        away_payload = request.data.get("away_lineup_data")

        with transaction.atomic():
            if home_payload:
                # if id provided, fetch and reassign; otherwise create a new TeamLineUp and set
                home_serializer = TeamLineUpCreateSerializer(data=home_payload)
                home_serializer.is_valid(raise_exception=True)
                new_home = home_serializer.save() if not home_payload.get("id") else TeamLineUpModel.objects.get(
                    pk=home_payload["id"])
                if str(new_home.team.pk) != str(match.home_team.pk):
                    return Response({"detail": "home_lineup team does not match match.home_team"},
                                    status=status.HTTP_400_BAD_REQUEST)
                match_lineup.home_lineup = new_home

            if away_payload:
                away_serializer = TeamLineUpCreateSerializer(data=away_payload)
                away_serializer.is_valid(raise_exception=True)
                new_away = away_serializer.save() if not away_payload.get("id") else TeamLineUpModel.objects.get(
                    pk=away_payload["id"])
                if str(new_away.team.pk) != str(match.away_team.pk):
                    return Response({"detail": "away_lineup team does not match match.away_team"},
                                    status=status.HTTP_400_BAD_REQUEST)
                match_lineup.away_lineup = new_away

            match_lineup.save()
            return Response(MatchLineUpSerializer(match_lineup).data)
