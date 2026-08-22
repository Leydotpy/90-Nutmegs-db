from rest_framework import generics, permissions

from api.rest.core import get_model
from api.rest.dashboard.permissions import IsOwnerOrReadOnly
from api.rest.web.serializers.comments import *

Post = get_model("posts", "Post")
Comment = get_model("comments", "Comment")


class CommentCreateAPIView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Comment.objects.all()

    def get_serializer_class(self):
        model_type = self.request.GET.get("model_type")
        slug = self.request.GET.get("slug")
        parent_id = self.request.GET.get("parent_id", None)
        return comment_create_func(
            model_type=model_type, slug=slug,
            parent_id=parent_id, user=self.request.user
        )


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentDetailSerializer
    queryset = Comment.objects.filter(id__gte=0)
    permission_classes = [IsOwnerOrReadOnly]
