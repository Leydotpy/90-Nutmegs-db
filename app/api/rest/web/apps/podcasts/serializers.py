from django.apps import apps
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from api.rest.fields import TagsField
from api.rest.web.serializers.auth import UserDisplaySerializer
from api.rest.web.serializers.comments import CommentDetailSerializer
from api.rest.web.serializers.media import ImageModelSerializer
from apps.memberships.access import AccessService
from apps.posts.models import PostReaction
from apps.posts.podcasts.models import Podcast, Episode, PlayBack
from apps.promotions.models import AutomaticPostList, HandPickedPostList, Image as PromotionImage
from utils.utils import get_client_ip


class AppLabel(models.TextChoices):
    PODCAST = "podcasts.Podcast", _("Podcast")
    EPISODE = "podcasts.Episode", _("Episode")
    PLAYLIST = "media.Playlist", _("Playlist")


class PostReactionSerializer(serializers.ModelSerializer):
    user = UserDisplaySerializer(read_only=True)

    class Meta:
        model = PostReaction
        fields = ("id", "user", "reaction", "object_id")


class PodcastListSerializer(serializers.ModelSerializer):
    image = ImageModelSerializer(source="get_image_url", read_only=True)
    type = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    duration = serializers.CharField(source="duration_string", read_only=True)
    raw_duration = serializers.IntegerField(source="get_raw_duration", read_only=True)
    tags = TagsField(read_only=True, render_as_list=False)

    class Meta:
        model = Podcast
        fields = (
            "id", "title", "subtitle", "duration", "structure", "type", "tags", "raw_duration",
            "description", "slug", "timestamp", "is_liked", "image",
        )

    def get_type(self, obj):
        return f"{obj._meta.app_label}.{obj.__class__.__name__}"

    def get_is_liked(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            # Assuming check_is_liked is defined on BasePost or a Mixin
            return getattr(obj, 'check_is_liked', lambda u: False)(user)
        return False


class EpisodeListSerializer(serializers.ModelSerializer):
    image = ImageModelSerializer(source="get_image", read_only=True)
    type = serializers.CharField(source="get_type")
    is_liked = serializers.SerializerMethodField("get_is_liked")
    duration = serializers.CharField(read_only=True)
    raw_duration = serializers.IntegerField(source="get_raw_duration", read_only=True)
    hosts = TagsField(read_only=True, render_as_list=False)
    tags = TagsField(read_only=True, render_as_list=False)

    class Meta:
        model = Episode
        fields = (
            "id",
            "title",
            "subtitle",
            "slug",
            "type",
            "timestamp",
            "is_liked",
            "description",
            "exclusive",
            "public_release_date",
            "hosts",
            "tags",
            "raw_duration",
            "duration",
            "image",
        )

        read_only_fields = tuple()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return obj.check_is_liked(request.user)


class EpisodeDetailSerializer(EpisodeListSerializer):
    comments = CommentDetailSerializer(source="get_comments", many=True)
    podcast = PodcastListSerializer()
    reactions = PostReactionSerializer(source="get_reactions", many=True)
    my_reaction = serializers.SerializerMethodField("get_my_reaction")
    user_has_subscribed = serializers.SerializerMethodField()
    user_has_access = serializers.SerializerMethodField()
    downloadable = serializers.SerializerMethodField()

    class Meta(EpisodeListSerializer.Meta):
        fields = EpisodeListSerializer.Meta.fields + (
            "user_has_subscribed",
            "my_reaction",
            "podcast",
            "comments",
            "user_has_access",
            "reactions",
            "downloadable",
        )

        read_only_fields = EpisodeListSerializer.Meta.read_only_fields + ("podcast",)

    def get_my_reaction(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return None
        return PostReactionSerializer(
            obj.get_my_reaction(request.user),
            context={"request": request}).data

    def get_user_has_subscribed(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return obj.user_has_subscribed(request.user) or obj.podcast.user_has_subscribed(request.user)

    def get_user_has_access(self, obj):
        return AccessService().has_access(
            self.context["request"].user,
            obj
        )

    def get_downloadable(self, obj):
        return obj.is_downloadable_by(
            user=self.context["request"].user
        )


class PodcastDetailSerializer(PodcastListSerializer):
    """
    Extends ListSerializer to add detailed fields.
    Expects 'paginated_episodes' in context for the episodes list.
    """
    comments = CommentDetailSerializer(source="get_comments", many=True, read_only=True)
    seasons = serializers.SerializerMethodField()
    episodes = serializers.SerializerMethodField()
    subscriptions = UserDisplaySerializer(source="subscribers", many=True, read_only=True)
    parent = PodcastListSerializer(read_only=True)

    # Additional fields
    reactions = PostReactionSerializer(source="get_reactions", many=True, read_only=True)
    my_reaction = serializers.SerializerMethodField()
    user_has_subscribed = serializers.SerializerMethodField()

    class Meta(PodcastListSerializer.Meta):
        fields = PodcastListSerializer.Meta.fields + (
            "episodes", "seasons", "reactions", "my_reaction",
            "comments", "subscriptions", "parent", "user_has_subscribed"
        )

    def get_seasons(self, obj):
        """Returns serialized children (seasons) if they exist."""
        seasons = obj.get_seasons()
        if seasons.exists():
            return PodcastListSerializer(seasons, many=True, context=self.context).data
        return None

    def get_episodes(self, obj):
        """
        Returns the paginated episodes dictionary passed from the View.
        This avoids putting pagination logic inside the serializer.
        """
        return self.context.get('paginated_episodes')

    def get_my_reaction(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            reaction = obj.get_my_reaction(user)
            if reaction:
                return PostReactionSerializer(reaction, context=self.context).data
        return None

    def get_user_has_subscribed(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None:
            return False
        return obj.user_has_subscribed(user)


class HandPickedPodcastPromotionSerializers(serializers.ModelSerializer):
    items = PodcastListSerializer(source="get_objects", many=True)
    url = serializers.URLField(source="link_url")
    text = serializers.CharField(source="link_text")

    class Meta:
        model = HandPickedPostList
        fields = ("name", "description", "subtitle", "items", "text", "url")


class AutomaticPodcastPromotionSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    url = serializers.URLField(source="link_url")
    text = serializers.CharField(source="link_text")

    class Meta:
        model = AutomaticPostList
        fields = ("name", "description", "subtitle", "text", "url", "items",)

    def get_items(self, obj: AutomaticPostList):
        user = self.context["request"].user
        return EpisodeDetailSerializer(obj.get_objects(user=user), many=True, context=self.context).data


class PromotionSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    subtitle = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    text = serializers.CharField(required=False)
    url = serializers.CharField(required=False)
    items = serializers.ListField()


class ImageBannerPromotionSerializer(serializers.ModelSerializer):
    resource_id = serializers.CharField(source="pk", read_only=True)
    url = serializers.URLField(source="banner_url")
    podcast_id = serializers.UUIDField(source="podcast_id", read_only=True)

    class Meta:
        model = PromotionImage
        fields = (
            "resource_id",
            "name",
            "title",
            "description",
            "cta_text",
            "url",
            "podcast_id",
            "banner_output_format",
            "banner_status",
        )


class SubscribeSerializer(serializers.Serializer):
    app_label = serializers.ChoiceField(choices=AppLabel.choices, default=AppLabel.PODCAST)
    item_id = serializers.CharField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = None

    def validate(self, attrs):
        if not self.user.is_authenticated:
            raise serializers.ValidationError("Please login to subscribe")
        try:
            model = apps.get_model(attrs["app_label"])
        except Exception as e:
            raise serializers.ValidationError(str(e))
        self._model = get_object_or_404(model, id=attrs["item_id"])
        return attrs

    @property
    def user(self):
        return self.context["request"].user

    def create(self, validated_data):
        is_subscribed = getattr(self._model, 'toggle_subscription')(self.user)
        return {"is_subscribed": is_subscribed}


class PlayBackModelSerializer(serializers.ModelSerializer):
    percentage_completed = serializers.IntegerField(source="get_percentage_completed")
    remaining_minutes = serializers.IntegerField(source="get_remaining_minutes")
    episode = EpisodeDetailSerializer(read_only=True)

    class Meta:
        model = PlayBack
        fields = (
            "id",
            "is_completed",
            "current_timestamp",
            "last_played_at",
            "percentage_completed",
            "remaining_minutes",
            "episode"
        )


class PlayBackUpdateSerializer(serializers.Serializer):
    seconds = serializers.IntegerField(required=True)
    is_completed = serializers.BooleanField(default=False)

    @property
    def request(self):
        return self.context["request"]

    @property
    def user(self):
        return self.request.user

    def update(self, instance, validated_data):
        if not self.user.is_authenticated:
            return {"success": False, "message": "You are not logged in"}
        playback = PlayBack.objects.update_progress(
            user=self.context["request"].user,
            seconds=validated_data["seconds"],
            is_completed=validated_data["is_completed"],
            episode_id=instance.id,
            ip_address=get_client_ip(request=self.request)
        )
        return {"success": True, "seconds": playback.current_timestamp}
