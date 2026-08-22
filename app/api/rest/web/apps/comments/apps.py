from django.urls import path
from django.utils.translation import gettext_lazy as _

from core.application import AppConfig


class CommentWebAPIConfig(AppConfig):
    label = "comment_web_api"
    name = "api.rest.web.apps.comments"
    verbose_name = _("Comment Web Api")

    namespace = "comment_web_api"


    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        from api.rest.web.apps.comments.views import (
            CommentCreateAPIView,
        )
        self.create = CommentCreateAPIView


    def get_urls(self):
        urls = [
            path("create/", self.create.as_view(), name="create"),
        ]
        return self.post_process_urls(urls)
