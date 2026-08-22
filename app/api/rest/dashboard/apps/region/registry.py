from api.rest.dashboard.registry import ResourceRegistry, ResourceConfig
from apps.region.leagues.clubs.models import Team
from apps.region.leagues.models import League
from apps.region.models import Country
from .serializers import CountrySerializer, LeagueModelSerializer, TeamModelSerializer

region_registry = ResourceRegistry()


# ----------------------------------------
# Decorator-style registration examples
# ----------------------------------------
@region_registry.register("countries")
def _countries_config():
    # lambda kept lazy so imports of ORM are safe at import time
    return ResourceConfig(
        serializer=CountrySerializer,
        queryset_factory=lambda self: Country.objects.all(),
        scope_field="region_id",
    )


@region_registry.register("leagues")
def _leagues_config():
    return ResourceConfig(
        serializer=LeagueModelSerializer,
        queryset_factory=lambda self: League.objects.all(),
        scope_field="region_id",
    )


# class-based factory also works (callable)
@region_registry.register("teams")
def _teams_config():
    return ResourceConfig(
        serializer=TeamModelSerializer,
        queryset_factory=lambda self_: Team.objects.all(),
        scope_field="league_id",  # example FK
    )
