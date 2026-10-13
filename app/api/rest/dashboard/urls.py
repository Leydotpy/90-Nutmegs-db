from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from api.rest.dashboard.permissions import ActiveStaff

urlpatterns = [
    path("apps/", ("api.rest.dashboard.apps.urls", "dashboard_apps_api", None)),
    path("schema/", SpectacularAPIView.as_view(permission_classes=[ActiveStaff]), name="schema"),
    path(
        "schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[ActiveStaff]),
        name="swagger-ui",
    ),
    path(
        "schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema", permission_classes=[ActiveStaff]),
        name="redoc",
    ),
]
