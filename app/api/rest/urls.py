from django.urls import path

urlpatterns = [
    path("web/", ("api.rest.web.urls", "rest_web", None)),
    path("dashboard/", ("api.rest.dashboard.urls", "dashboard_api", None)),
]
