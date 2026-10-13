from django.urls import path

from api.rest.web.apps.comments.views import CommentCreateAPIView

app_name = "comment_web_api"

urlpatterns = [path("create/", CommentCreateAPIView.as_view(), name="create")]
