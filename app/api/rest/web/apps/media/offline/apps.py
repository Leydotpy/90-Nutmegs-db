from django.urls import path
from django.utils.translation import gettext_lazy as _

from core.application import AppConfig


class MediaOfflineWebAPIConfig(AppConfig):
    label = "media_offline_web_api"
    name = "api.rest.web.apps.media.offline"
    verbose_name = _("Media Offline Web Api")

    namespace = "media_offline_web_api"

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.register_device_view = None
    #     self.request_offline_package_view = None
    #     self.packaging_status_view = None
    #     self.revoke_license_view = None

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        from api.rest.web.apps.media.offline.views import (
            register_device,
            request_offline_package,
            packaging_status,
            revoke_license
        )

        self.register_device_view = register_device
        self.request_offline_package_view = request_offline_package
        self.packaging_status_view = packaging_status
        self.revoke_license_view = revoke_license

    def get_urls(self):
        urls = [
            path("devices/register/", self.register_device_view, name="register_device"),
            path("packages/request/", self.request_offline_package_view, name="request_offline_package"),
            path("packages/status/<str:task_id>/", self.packaging_status_view, name="packaging_status"),
            path("licenses/<uuid:license_id>/revoke/", self.revoke_license_view, name="revoke_offline_license"),
        ]
        return self.post_process_urls(urls)
