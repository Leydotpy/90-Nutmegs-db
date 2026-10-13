from django.urls import include, path

from api.rest.web.views import ExploreAPIView

urlpatterns = [
    path("apps/", include("api.rest.web.apps.urls")),
    path("explore/", ExploreAPIView.as_view(), name="explore"),
]
