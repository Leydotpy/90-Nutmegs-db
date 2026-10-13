from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers as ser

from apps.comments.models import Comment
from api.rest.web.serializers.auth import UserDisplaySerializer

User = settings.AUTH_USER_MODEL


def comment_create_func(model_type="post", slug=None, parent_id=None, user=None):
    class CommentCreateSerializer(ser.ModelSerializer):
        user = UserDisplaySerializer(read_only=True)
        replies = CommentChildSerializer(many=True, read_only=True, source="children")
        class Meta:
            model = Comment
            fields = ('content', 'comment_type', 'media', 'user', 'replies')

        def __init__(self, **kwargs):
            self.model_type = model_type
            self.slug = slug
            self.parent_obj = None
            self.object_id = None
            self.user = user
            if parent_id:
                parent = Comment.objects.get(id=parent_id)
                if parent:
                    self.parent_obj = parent
            super().__init__(**kwargs)


        def validate(self, attrs):
            if not self.model_type:
                raise ser.ValidationError({"model_type": "A model type is required."})
            if not self.slug:
                raise ser.ValidationError({"slug": "A slug is required."})

            try:
                content_type = ContentType.objects.get(model=str(self.model_type).lower())
            except ContentType.DoesNotExist:
                raise ser.ValidationError(
                    {"object": f"The {self.model_type} you are commenting on does no longer exist"})

            model = content_type.model_class()
            try:
                obj = model.objects.get(slug=self.slug)
            except ObjectDoesNotExist:
                raise ser.ValidationError({f"{self.model_type}": "This object does not exist"})

            self.object_id = obj.pk
            return attrs

        def create(self, validated_data):
            return Comment.objects.create_by_model_type(
                object_id=self.object_id,
                content=validated_data.get("content"),
                comment_type=validated_data.get("comment_type", Comment.Type.TEXT),
                media=validated_data.get("media"),
                parent_obj=self.parent_obj,
                model_type=self.model_type,
                user=self.user
            )

    return CommentCreateSerializer


class CommentChildSerializer(ser.ModelSerializer):
    user = UserDisplaySerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'user', 'content', 'timestamp')


class CommentDetailSerializer(ser.ModelSerializer):
    user = UserDisplaySerializer(read_only=True)
    reply_count = ser.IntegerField(read_only=True, source="replies_count")
    # content_object_url = ser.SerializerMethodField()
    replies = CommentChildSerializer(many=True, read_only=True, source="children")

    class Meta:
        model = Comment
        fields = ("id", "user", "content", "reply_count", "replies", "timestamp")
        read_only_fields = [
            "reply_count",
            "replies",
        ]
