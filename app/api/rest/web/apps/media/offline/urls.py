from django.urls import path

from api.rest.web.apps.media.offline.views import (
    packaging_status,
    register_device,
    request_offline_package,
    revoke_license,
)

app_name = "media_offline_web_api"

urlpatterns = [
    path("devices/register/", register_device, name="register_device"),
    path("packages/request/", request_offline_package, name="request_offline_package"),
    path("packages/status/<str:task_id>/", packaging_status, name="packaging_status"),
    path(
        "licenses/<uuid:license_id>/revoke/",
        revoke_license,
        name="revoke_offline_license",
    ),
]
