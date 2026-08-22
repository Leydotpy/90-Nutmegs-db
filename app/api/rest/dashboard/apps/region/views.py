from typing import Optional

from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample,
)
from rest_framework import viewsets, status, permissions, filters, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from api.rest.dashboard.apps.region.serializers import (
    RegionSerializer,
    CountrySerializer, CountryCreateSerializer, CountryUpdateSerializer,
    LeagueSerializer, LeagueCreateSerializer, LeagueUpdateSerializer,
    TeamSerializer, TeamCreateSerializer, TeamUpdateSerializer, LeagueModelSerializer, TeamModelSerializer,
)
# import the permission factory
from api.rest.permissions import ModelPermissionRequired
from apps.region.leagues.clubs.models import Team
from apps.region.leagues.models import League
from apps.region.models import Region, Country

from .registry import region_registry


class RegionViewSet(viewsets.ModelViewSet):
    """
    RegionViewSet: primary resource for Region. All Country/League/Team creation & management
    is available via nested actions on this viewset.
    """
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "timestamp"]

    # ---------- helpers included in the class ----------
    @staticmethod
    def _get_country_or_404(region, country_id):
        return get_object_or_404(
            Country.objects.select_related('region'),
            pk=country_id,
            region_id=region.id
        )

    @staticmethod
    def _get_league_or_404(region, country_id, league_id):
        return get_object_or_404(
            League.objects.select_related('region', 'region__region'),
            pk=league_id,
            region__id=country_id,
            region__region_id=region.id
        )

    @staticmethod
    def _get_team_or_404(region, country_id, league_id, team_id):
        return get_object_or_404(
            Team.objects.select_related('league', 'league__region'),
            pk=team_id,
            league__id=league_id,
            league__region__id=country_id,
            league__region__region_id=region.id
        )

    # ----------------- examples (request + response) -----------------
    COUNTRY_POST_EXAMPLE = OpenApiExample(
        "Create Country (example request)",
        value={"name": "Nigeria", "code": 566},
        request_only=True,
        summary="Create a country under the region",
    )
    COUNTRIES_LIST_EXAMPLE = OpenApiExample(
        "Countries list (example response)",
        value=[{
            "id": "6a1f0f5b-0000-4d2f-8f9a-111111111111",
            "region": "7b2f0f5b-0000-4d2f-8f9a-222222222222",
            "name": "Nigeria",
            "slug": "6a1f0f5b-nigeria",
            "code": 566,
            "timestamp": "2025-01-01T12:34:56Z"
        }],
        response_only=True,
        summary="Example countries response"
    )
    COUNTRY_DETAIL_EXAMPLE = OpenApiExample(
        "Country detail (example response)",
        value={
            "id": "6a1f0f5b-0000-4d2f-8f9a-111111111111",
            "region": "7b2f0f5b-0000-4d2f-8f9a-222222222222",
            "name": "Nigeria",
            "slug": "6a1f0f5b-nigeria",
            "code": 566,
            "timestamp": "2025-01-01T12:34:56Z"
        },
        response_only=True,
        summary="Example country detail"
    )

    LEAGUE_POST_EXAMPLE = OpenApiExample(
        "Create League (example request)",
        value={"region": "6a1f0f5b-0000-4d2f-8f9a-111111111111", "name": "Super League", "short_name": "SPL",
               "code": 1234},
        request_only=True,
        summary="Create a league targeted at a country (use the country's id in `region`)",
    )
    LEAGUES_LIST_EXAMPLE = OpenApiExample(
        "Leagues list (example response)",
        value=[{
            "id": "8c3f0f5b-0000-4d2f-8f9a-333333333333",
            "region": "6a1f0f5b-0000-4d2f-8f9a-111111111111",
            "name": "Super League",
            "short_name": "SPL",
            "slug": "8c3f0f5b-super-league",
            "code": 1234,
            "timestamp": "2025-01-01T12:34:56Z",
            "popularity": 10
        }],
        response_only=True,
        summary="Example leagues response"
    )
    LEAGUE_DETAIL_EXAMPLE = OpenApiExample(
        "League detail (example response)",
        value={
            "id": "8c3f0f5b-0000-4d2f-8f9a-333333333333",
            "region": "6a1f0f5b-0000-4d2f-8f9a-111111111111",
            "name": "Super League",
            "short_name": "SPL",
            "slug": "8c3f0f5b-super-league",
            "code": 1234,
            "timestamp": "2025-01-01T12:34:56Z",
            "popularity": 10
        },
        response_only=True,
        summary="Example league detail"
    )

    TEAM_POST_EXAMPLE = OpenApiExample(
        "Create Team (example request)",
        value={"league": "8c3f0f5b-0000-4d2f-8f9a-333333333333", "name": "FC Example", "short_name": "FCE",
               "code": 4321},
        request_only=True,
        summary="Create a team for a league (ensure the league belongs to a country in the region)",
    )
    TEAMS_LIST_EXAMPLE = OpenApiExample(
        "Teams list (example response)",
        value=[{
            "id": "9d4f0f5b-0000-4d2f-8f9a-444444444444",
            "league": "8c3f0f5b-0000-4d2f-8f9a-333333333333",
            "name": "FC Example",
            "short_name": "FCE",
            "slug": "9d4f0f5b-fc-example",
            "code": 4321,
            "popularity": 5,
            "timestamp": "2025-01-01T12:34:56Z"
        }],
        response_only=True,
        summary="Example teams response"
    )
    TEAM_DETAIL_EXAMPLE = OpenApiExample(
        "Team detail (example response)",
        value={
            "id": "9d4f0f5b-0000-4d2f-8f9a-444444444444",
            "league": "8c3f0f5b-0000-4d2f-8f9a-333333333333",
            "name": "FC Example",
            "short_name": "FCE",
            "slug": "9d4f0f5b-fc-example",
            "code": 4321,
            "popularity": 5,
            "timestamp": "2025-01-01T12:34:56Z"
        },
        response_only=True,
        summary="Example team detail"
    )

    # --------------------------
    # Countries (list/create)
    # --------------------------
    @extend_schema(
        summary="List or create countries for a region",
        description="GET lists all countries for this region. POST creates a new country under the region.",
        responses={200: OpenApiResponse(response=CountrySerializer(many=True)),
                   201: OpenApiResponse(response=CountrySerializer)},
        examples=[COUNTRY_POST_EXAMPLE, COUNTRIES_LIST_EXAMPLE],
        methods=["GET", "POST"],
    )
    @action(
        detail=True,
        methods=["get", "post"],
        url_path="countries",
        throttle_classes=[ScopedRateThrottle],
        # throttle_scope="region_countries_write",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def countries(self, request, pk=None):
        region = self.get_object()

        if request.method == "GET":
            qs = region.countries.all()
            page = self.paginate_queryset(qs)
            ser = CountrySerializer(page or qs, many=True, context={"request": request})
            return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

        # POST -> create a country under this region
        if not request.user or not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = CountryCreateSerializer(data=request.data, context={"region": region})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            country = serializer.save()
        return Response(CountrySerializer(country).data, status=status.HTTP_201_CREATED)

    # --------------------------
    # Country detail (manage)
    # --------------------------
    @extend_schema(
        summary="Retrieve/modify/delete a country inside this region",
        parameters=[OpenApiParameter("country_id", required=True, description="Country id")],
        responses={200: OpenApiResponse(response=CountrySerializer)},
        examples=[COUNTRY_DETAIL_EXAMPLE],
    )
    @action(
        detail=True,
        methods=["get", "put", "patch", "delete"],
        url_path=r"countries/(?P<country_id>[^/.]+)",
        throttle_classes=[ScopedRateThrottle],
        # throttle_scope="region_countries_write",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def country_detail(self, request, pk=None, country_id=None):
        region = self.get_object()
        country = get_object_or_404(Country, pk=country_id)

        # ownership check
        if country.region_id != region.id:
            return Response({"detail": "Country does not belong to this region."}, status=status.HTTP_400_BAD_REQUEST)

        # GET
        if request.method == "GET":
            return Response(CountrySerializer(country).data)

        # PUT / PATCH
        if request.method in ("PUT", "PATCH"):
            if not request.user or not request.user.is_authenticated:
                return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            serializer = CountryUpdateSerializer(country, data=request.data, partial=(request.method == "PATCH"))
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                serializer.save()
            return Response(CountrySerializer(country).data)

        # DELETE -> require model-level permission
        if request.method == "DELETE":
            if not request.user or not request.user.is_authenticated:
                return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

            # use the permission helper class for model-level permission check
            perm_cls = ModelPermissionRequired('delete')
            perm = perm_cls()
            if not perm.has_object_permission(request, self, country):
                # compute expected permission string for clarity
                perm_str = f"{country._meta.app_label}.delete_{country._meta.model_name}"
                return Response({"detail": f"Permission required: {perm_str}"}, status=status.HTTP_403_FORBIDDEN)

            with transaction.atomic():
                country.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    # --------------------------
    # Leagues (list/create)
    # --------------------------
    @extend_schema(
        summary="List or create leagues for the region (leagues are created against a Country)",
        description="POST requires 'region' field containing the country id (the serializer uses name 'region' for country id). The view will ensure the country belongs to this region.",
        responses={200: OpenApiResponse(response=LeagueSerializer(many=True)),
                   201: OpenApiResponse(response=LeagueSerializer)},
        examples=[LEAGUE_POST_EXAMPLE, LEAGUES_LIST_EXAMPLE],
        methods=["GET", "POST"],
    )
    @action(
        detail=True,
        methods=["get", "post"],
        url_path="countries/(?P<country_id>[^/.]+)/leagues",
        throttle_classes=[ScopedRateThrottle],
        # throttle_scope="region_leagues_write",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def leagues(self, request, *, pk=None, country_id=None):
        region = self.get_object()

        if request.method == "GET":
            qs = League.objects.filter(region__region=region).select_related('region')
            page = self.paginate_queryset(qs)
            serializer = LeagueModelSerializer(page or qs, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

        # POST -> create league for a given country in region
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication required")

        # validate country exists in region (single query)
        country = self._get_country_or_404(region, country_id)

        serializer = LeagueCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # create with explicit FK to country
        with transaction.atomic():
            league = serializer.save(region=country)
        return Response(LeagueSerializer(league).data, status=status.HTTP_201_CREATED)

    # --------------------------
    # League detail (manage)
    # --------------------------
    @extend_schema(
        summary="Retrieve/modify/delete a league (must belong to a country in the region)",
        parameters=[OpenApiParameter("league_id", required=True)],
        responses={200: OpenApiResponse(response=LeagueSerializer)},
        examples=[LEAGUE_DETAIL_EXAMPLE],
    )
    @action(
        detail=True,
        methods=["get", "put", "patch", "delete"],
        url_path=r"countries/(?P<country_id>[^/.]+)/leagues/(?P<league_id>[^/.]+)",
        throttle_classes=[ScopedRateThrottle],
        # throttle_scope="region_leagues_write",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def league_detail(self, request, *, pk=None, country_id=None, league_id=None):
        region = self.get_object()
        league = self._get_league_or_404(region, country_id, league_id)

        if request.method == "GET":
            return Response(LeagueModelSerializer(league).data)

        if request.method in ("PUT", "PATCH"):
            if not request.user or not request.user.is_authenticated:
                raise NotAuthenticated("Authentication required")
            serializer = LeagueUpdateSerializer(league, data=request.data, partial=(request.method == "PATCH"))
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                serializer.save()
            return Response(LeagueSerializer(league).data)

        # DELETE -> model-level permission check
        if request.method == "DELETE":
            if not request.user or not request.user.is_authenticated:
                raise NotAuthenticated("Authentication required")

            perm_cls = ModelPermissionRequired('delete')
            perm = perm_cls()
            if not perm.has_object_permission(request, self, league):
                perm_str = f"{league._meta.app_label}.delete_{league._meta.model_name}"
                raise PermissionDenied(detail=f"Permission required: {perm_str}")

            with transaction.atomic():
                league.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    # --------------------------
    # Teams (list/create)
    # --------------------------
    @extend_schema(
        summary="List or create teams inside this region",
        description="GET lists all teams whose league is in a country that belongs to this region. POST creates a team for a given league; the view ensures the league's country belongs to the region.",
        responses={200: OpenApiResponse(response=TeamSerializer(many=True)),
                   201: OpenApiResponse(response=TeamSerializer)},
        examples=[TEAM_POST_EXAMPLE, TEAMS_LIST_EXAMPLE],
        methods=["GET", "POST"],
    )
    @action(
        detail=True,
        methods=["get", "post"],
        url_path="countries/(?P<country_id>[^/.]+)/leagues/(?P<league_id>[^/.]+)/teams",
        throttle_classes=[ScopedRateThrottle],
        # throttle_scope="region_teams_write",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def teams(self, request, *, pk=None, country_id=None, league_id=None):
        region = self.get_object()

        if request.method == "GET":
            # filter to teams in this region (use indexed columns)
            qs = Team.objects.filter(league__region__region=region).select_related('league')
            page = self.paginate_queryset(qs)
            serializer = TeamModelSerializer(page or qs, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

        # POST -> create team under league
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication required")

        league = self._get_league_or_404(region, country_id, league_id)

        serializer = TeamCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            team = serializer.save(league=league)
        return Response(TeamSerializer(team).data, status=status.HTTP_201_CREATED)

    # --------------------------
    # Team detail (manage)
    # --------------------------
    @extend_schema(
        summary="Retrieve/modify/delete a team (must belong to a league in this region)",
        parameters=[OpenApiParameter("team_id", required=True)],
        responses={200: OpenApiResponse(response=TeamSerializer)},
        examples=[TEAM_DETAIL_EXAMPLE],
    )
    @action(
        detail=True,
        methods=["get", "put", "patch", "delete"],
        url_path=r"countries/(?P<country_id>[^/.]+)/leagues/(?P<league_id>[^/.]+)/teams/(?P<team_id>[^/.]+)",
        throttle_classes=[ScopedRateThrottle],
        # throttle_scope="region_teams_write",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def team_detail(self, request, *, pk=None, country_id=None, league_id=None, team_id=None):
        region = self.get_object()
        # ensure league exists + belongs to region
        league = self._get_league_or_404(region, country_id, league_id)
        # now fetch team belonging to that league
        team = self._get_team_or_404(region, country_id, league_id, team_id)

        if request.method == "GET":
            return Response(TeamSerializer(team).data)

        if request.method in ("PUT", "PATCH"):
            if not request.user or not request.user.is_authenticated:
                raise NotAuthenticated("Authentication required")
            serializer = TeamUpdateSerializer(team, data=request.data, partial=(request.method == "PATCH"))
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                serializer.save()
            return Response(TeamSerializer(team).data)

        # DELETE -> model-level permission
        if request.method == "DELETE":
            if not request.user or not request.user.is_authenticated:
                raise NotAuthenticated("Authentication required")
            perm_cls = ModelPermissionRequired('delete')
            perm = perm_cls()
            if not perm.has_object_permission(request, self, team):
                perm_str = f"{team._meta.app_label}.delete_{team._meta.model_name}"
                raise PermissionDenied(detail=f"Permission required: {perm_str}")
            with transaction.atomic():
                team.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class GenericRegionView(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "timestamp"]
    http_method_names = ["get"]

    default_serializer = RegionSerializer
    default_queryset_factory = staticmethod(lambda self: Region.objects.all())

    def _infer_key(self) -> Optional[str]:
        """
        Best-effort inference: prefer resolver_match.url_name then fall back to path suffix.
        This keeps the view robust and registry-agnostic.
        """
        resolver = getattr(self.request, "resolver_match", None)
        if resolver and resolver.url_name:
            url_name = resolver.url_name
            for key in region_registry.keys():
                if key in url_name:
                    return key

        path = self.request.path.rstrip("/")
        for key in region_registry.keys():
            if path.endswith(f"/{key}"):
                return key
        return None

    def get_serializer_class(self):
        key = self._infer_key()
        cfg = region_registry.get(key) if key else None
        return cfg.serializer if cfg else self.default_serializer

    def get_queryset(self):
        key = self._infer_key()
        cfg = region_registry.get(key) if key else None
        if cfg:
            qs = cfg.queryset_factory(self)
            parent_id = self.kwargs.get("region_pk") or self.kwargs.get("pk")
            if parent_id and cfg.scope_field:
                try:
                    return qs.filter(**{cfg.scope_field: parent_id})
                except Exception:
                    # safe fallback if scoping fails (e.g. FK name differs)
                    return qs
            return qs
        return self.default_queryset_factory(self)

    @action(
        detail=True,
        url_path="countries",
        throttle_classes = [ScopedRateThrottle],
        permission_classes = [permissions.IsAuthenticatedOrReadOnly],
        methods=["get"]
    )
    def countries(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(
        detail=True,
        url_path="leagues",
        throttle_classes = [ScopedRateThrottle],
        permission_classes = [permissions.IsAuthenticatedOrReadOnly],
        methods=["get"]
    )
    def leagues(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(
        detail=True,
        url_path="teams",
        throttle_classes = [ScopedRateThrottle],
        permission_classes = [permissions.IsAuthenticatedOrReadOnly],
        methods=["get"]
    )
    def teams(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

class CountryListAPIView(ListAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    throttle_classes = [ScopedRateThrottle]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LeagueListAPIView(ListAPIView):
    queryset = League.objects.all()
    serializer_class = LeagueModelSerializer
    throttle_classes = [ScopedRateThrottle]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class TeamListAPIView(ListAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamModelSerializer
    throttle_classes = [ScopedRateThrottle]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]