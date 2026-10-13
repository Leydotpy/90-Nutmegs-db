from django.urls import include, path

urlpatterns = [
    path("matches/", ("api.rest.dashboard.apps.match.urls", "match_dashboard_api", None)),
    path(
        "memberships/",
        include("api.rest.dashboard.apps.memberships.urls", namespace="memberships"),
    ),
    path("podcasts/", ("api.rest.dashboard.apps.podcasts.urls", "podcasts_dashboard_api", None)),
    path("promotions/", include("api.rest.dashboard.apps.promotions.urls")),
    path("persons/", ("api.rest.dashboard.apps.persons.urls", "persons_dashboard_api", None)),
    path("regions/", ("api.rest.dashboard.apps.region.urls", "region_dashboard_api", None)),
]
