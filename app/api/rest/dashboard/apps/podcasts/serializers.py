"""
podcast api serializers

Production-ready DRF serializers and viewsets for Podcast and Episode models,
taking into account AbstractAnalytics (countries, competitions, regions, teams,
players, matches) and BasePost (parent field).

Includes a DRF TagsField serializer (based on the user's implementation) and
helpers to correctly persist tags depending on the underlying model field type.

Drop this file into your project (e.g., apps/podcast/api/podcast_api_module.py)
and adjust import paths if your project layout differs.
"""

from apps.match.models import Match
from apps.persons.models import Player
from apps.posts.podcasts.models import Category, Episode, Podcast, Season
from apps.posts.podcasts.services import (
    CANONICAL_EPISODE_ACCESS_FIELDS,
    LEGACY_EPISODE_ACCESS_FIELDS,
    resolve_canonical_episode_owner,
    synchronize_episode_access_from_legacy,
    synchronize_episode_legacy_projection,
    synchronize_legacy_podcast_season,
)
from apps.region.leagues.clubs.models import Team
from apps.region.leagues.models import League
from apps.region.models import Country, Region
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import CharField, TextField
from rest_framework import serializers

from api.rest.dashboard.apps.category.serializers import CategorySerializer
from api.rest.dashboard.apps.match.serializers import MatchSerializer
from api.rest.dashboard.apps.media.audio.serializers import AudioSerializer
from api.rest.dashboard.apps.media.images.serializers import (
    ImageSerializer,
    _create_image_for_instance,
)
from api.rest.dashboard.apps.persons.serializers import PlayerSerializer
from api.rest.dashboard.apps.region.serializers import (
    CountrySerializer,
    LeagueModelSerializer,
    RegionSerializer,
    TeamModelSerializer,
)


# ------------------------
# DRF TagsField (from user)
# ------------------------
class TagsField(serializers.Field):
    """
    DRF field for CommaSeparatedCharField.
    Converts between DB string ("foo,bar,baz") and Python list internally.
    Can render as either a list or a comma-delimited string in API responses.
    """

    def __init__(self, *args, render_as_list=True, **kwargs):
        """
        :param render_as_list: If True, return a list in API output.
                               If False, return a comma-delimited string.
        """
        self.render_as_list = render_as_list
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        """
        Convert model field value into API output.
        """
        if value is None:
            return [] if self.render_as_list else ""

        # Normalize into list first
        if isinstance(value, list):
            items = [str(v).strip() for v in value if str(v).strip()]
        else:
            items = [v.strip() for v in str(value).split(",") if v.strip()]

        # Render based on option
        if self.render_as_list:
            return items
        return ",".join(items)

    def to_internal_value(self, data):
        """
        Convert incoming API data into Python list for the model.
        Accepts either a list or a comma-delimited string.
        """
        if isinstance(data, list):
            return [str(v).strip() for v in data if str(v).strip()]
        if isinstance(data, str):
            return [v.strip() for v in data.split(",") if v.strip()]
        raise serializers.ValidationError("Expected a list of strings or a comma-separated string.")


# ------------------------
# Helpers
# ------------------------
def _prepare_tags_for_model(model_class, tags_value):
    """
    Normalizes tags_value to the expected DB representation for the model field.
    If the model's 'tags' field is a CharField/TextField we join to comma string.
    If the model accepts lists (custom field), return the list.
    """
    if tags_value is None:
        return None

    # tags_value expected to be a list (TagsField.to_internal_value returns list)
    if not isinstance(tags_value, (list, tuple)):
        raise ValueError("tags_value must be a list or tuple")

    # try inspect model field
    try:
        field = model_class._meta.get_field("tags")
    except Exception:
        # if field not found, default to join
        return ",".join(tags_value)

    if isinstance(field, (CharField, TextField)):
        return ",".join(tags_value)
    # otherwise assume field accepts list-like, pass through
    return list(tags_value)


# ------------------------
# Serializers
# ------------------------


class PodcastSerializer(serializers.ModelSerializer):
    # tags handled by custom TagsField (returns list on to_internal_value)
    tags = TagsField(render_as_list=True, required=False, allow_null=True)

    # allow client to set analytic relationships by ID lists
    countries = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Country.objects.all(), required=False
    )
    competitions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=League.objects.all(), required=False
    )
    regions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Region.objects.all(), required=False
    )
    teams = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Team.objects.all(), required=False
    )
    players = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Player.objects.all(), required=False
    )
    matches = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Match.objects.all(), required=False
    )

    categories = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Category.objects.all(), required=False
    )
    subscriber_count = serializers.IntegerField(source="subscribers.count", read_only=True)

    images = ImageSerializer(
        many=True, read_only=True, source="get_images"
    )  # source calls Image.objects.filter_by_instance
    new_images = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text=(
            "List of image dictionaries to attach. Each may contain a title "
            "and an optional multipart file."
        ),
    )

    parent = serializers.PrimaryKeyRelatedField(
        queryset=Podcast.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Podcast  # set dynamically when importing into your app
        fields = [
            "id",
            "title",
            "subtitle",
            "structure",
            "description",
            "slug",
            "parent",
            "status",
            "explicit_content",
            "language",
            "website_url",
            "published_at",
            "tags",
            "categories",
            "images",
            "new_images",
            "countries",
            "competitions",
            "regions",
            "teams",
            "players",
            "matches",
            "view_count",
            "subscriber_count",
            "timestamp",
            "updated",
        ]
        read_only_fields = [
            "id",
            "slug",
            "view_count",
            "subscriber_count",
            "timestamp",
            "updated",
        ]

    def validate_parent(self, value):
        # Prevent an instance from being its own parent
        if self.instance and value and value.pk == getattr(self.instance, "pk", None):
            raise serializers.ValidationError("A podcast cannot be its own parent.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        structure = attrs.get("structure", getattr(self.instance, "structure", None))
        parent = attrs.get("parent", getattr(self.instance, "parent", None))

        if structure == Podcast.Structure.CHILD:
            if parent is None:
                raise serializers.ValidationError(
                    {"parent": "A child Podcast must have a parent Podcast."}
                )
            if parent.structure != Podcast.Structure.PARENT or parent.parent_id is not None:
                raise serializers.ValidationError(
                    {"parent": "A child Podcast must belong directly to a root parent Podcast."}
                )
        elif parent is not None:
            raise serializers.ValidationError({"parent": "Only a child Podcast may have a parent."})

        if self.instance is not None and structure != self.instance.structure:
            graph_is_materialized = (
                self.instance.children.exists()
                or self.instance.episodes.exists()
                or self.instance.seasons.exists()
                or Season.objects.filter(legacy_podcast=self.instance).exists()
            )
            if graph_is_materialized:
                raise serializers.ValidationError(
                    {
                        "structure": (
                            "Podcast structure cannot change after Seasons, child Podcasts, "
                            "or Episodes exist."
                        )
                    }
                )
        return attrs

    @staticmethod
    def _synchronize_legacy_season(instance):
        try:
            return synchronize_legacy_podcast_season(instance)
        except DjangoValidationError as exc:
            detail = getattr(exc, "message_dict", None) or {"parent": exc.messages}
            raise serializers.ValidationError(detail) from exc
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"parent": "The canonical Season conflicts with existing Season metadata."}
            ) from exc

    def create(self, validated_data):
        # Pop writable relationship lists and tags.
        countries = validated_data.pop("countries", [])
        competitions = validated_data.pop("competitions", [])
        regions = validated_data.pop("regions", [])
        teams = validated_data.pop("teams", [])
        players = validated_data.pop("players", [])
        matches = validated_data.pop("matches", [])
        categories = validated_data.pop("categories", [])
        tags = validated_data.pop("tags", None)
        new_images_data = validated_data.pop("new_images", [])

        with transaction.atomic():
            Podcast = self.Meta.model
            # prepare tags for model assignment (string or list depending on model field)
            if tags is not None:
                prepared_tags = _prepare_tags_for_model(Podcast, tags)
                validated_data["tags"] = prepared_tags

            instance = Podcast.objects.create(**validated_data)

            # set m2m fields
            if countries:
                instance.countries.set(countries)
            if competitions:
                instance.competitions.set(competitions)
            if regions:
                instance.regions.set(regions)
            if teams:
                instance.teams.set(teams)
            if players:
                instance.players.set(players)
            if matches:
                instance.matches.set(matches)
            if categories:
                instance.categories.set(categories)

            for img_payload in new_images_data:
                _create_image_for_instance(instance, img_payload)
            self._synchronize_legacy_season(instance)
            return instance

    def update(self, instance, validated_data):
        countries = validated_data.pop("countries", None)
        competitions = validated_data.pop("competitions", None)
        regions = validated_data.pop("regions", None)
        teams = validated_data.pop("teams", None)
        players = validated_data.pop("players", None)
        matches = validated_data.pop("matches", None)
        categories = validated_data.pop("categories", None)
        tags = validated_data.pop("tags", None)

        new_images_data = validated_data.pop("new_images", [])

        with transaction.atomic():
            Podcast = self.Meta.model
            if tags is not None:
                prepared_tags = _prepare_tags_for_model(Podcast, tags)
                instance.tags = prepared_tags

            # update simple fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # update m2m - if provided replace, else leave as-is
            if countries is not None:
                instance.countries.set(countries)
            if competitions is not None:
                instance.competitions.set(competitions)
            if regions is not None:
                instance.regions.set(regions)
            if teams is not None:
                instance.teams.set(teams)
            if players is not None:
                instance.players.set(players)
            if matches is not None:
                instance.matches.set(matches)
            if categories is not None:
                instance.categories.set(categories)

            if new_images_data:
                for img_payload in new_images_data:
                    _create_image_for_instance(instance, img_payload)
            self._synchronize_legacy_season(instance)
            return instance


class SeasonSerializer(serializers.ModelSerializer):
    """Canonical dashboard contract for explicit podcast seasons."""

    class Meta:
        model = Season
        fields = [
            "id",
            "podcast",
            "number",
            "title",
            "slug",
            "description",
            "position",
            "published_at",
            "legacy_podcast",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "legacy_podcast",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        podcast = attrs.get("podcast", getattr(self.instance, "podcast", None))
        if podcast is not None and (
            podcast.parent_id is not None or podcast.structure == Podcast.Structure.CHILD
        ):
            raise serializers.ValidationError(
                {"podcast": "A Season must belong to a root Podcast."}
            )
        return attrs


class EpisodeSerializer(serializers.ModelSerializer):
    tags = TagsField(render_as_list=True, required=False, allow_null=True)
    audio = AudioSerializer(many=True, required=False, allow_null=True, read_only=True)

    # analytics M2M
    countries = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Country.objects.all(), required=False
    )
    competitions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=League.objects.all(), required=False
    )
    regions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Region.objects.all(), required=False
    )
    teams = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Team.objects.all(), required=False
    )
    players = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Player.objects.all(), required=False
    )
    matches = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Match.objects.all(), required=False
    )

    categories = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Category.objects.all(), required=False
    )

    images = ImageSerializer(
        many=True, read_only=True, source="get_images"
    )  # source calls Image.objects.filter_by_instance
    new_images = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text=(
            "List of image dictionaries to attach. Each may contain a title "
            "and an optional multipart file."
        ),
    )

    class Meta:
        model = Episode
        fields = [
            "id",
            "podcast",
            "season",
            "audio",
            "title",
            "subtitle",
            "description",
            "slug",
            "episode_number",
            "episode_type",
            "explicit_content",
            "duration_seconds",
            "hosts",
            "tags",
            "public_release_date",
            "exclusive",
            "early_access_hours",
            "trend_score",
            "status",
            "visibility",
            "premium_available_at",
            "public_available_at",
            "required_plan",
            "preview_duration_seconds",
            "published_at",
            "view_count",
            "categories",
            "images",
            "new_images",
            "countries",
            "competitions",
            "regions",
            "teams",
            "players",
            "matches",
            "timestamp",
            "updated",
        ]
        read_only_fields = ["id", "slug", "trend_score", "view_count", "timestamp", "updated"]

    def _owner_values(self, attrs):
        podcast_supplied = "podcast" in attrs
        podcast = attrs.get("podcast", getattr(self.instance, "podcast", None))
        owner_changed = bool(
            podcast_supplied
            and (self.instance is None or podcast is None or podcast.pk != self.instance.podcast_id)
        )
        season = attrs.get(
            "season",
            None if owner_changed else getattr(self.instance, "season", None),
        )
        return podcast, season

    def validate(self, attrs):
        attrs = super().validate(attrs)
        podcast, season = self._owner_values(attrs)
        if podcast is None:
            return attrs

        if podcast.structure == Podcast.Structure.CHILD:
            parent = podcast.parent
            if (
                parent is None
                or parent.structure != Podcast.Structure.PARENT
                or parent.parent_id is not None
            ):
                raise serializers.ValidationError(
                    {"podcast": "The legacy child Podcast has no valid canonical parent."}
                )
            if season is not None and season.legacy_podcast_id != podcast.pk:
                raise serializers.ValidationError(
                    {"season": "The Season must represent the selected legacy child Podcast."}
                )
        elif podcast.parent_id is not None:
            raise serializers.ValidationError(
                {"podcast": "An Episode must belong to a root Podcast."}
            )
        elif season is not None and season.podcast_id != podcast.pk:
            raise serializers.ValidationError(
                {"season": "The season must belong to the selected podcast."}
            )
        return attrs

    def _resolve_owner(self, validated_data):
        podcast, season = self._owner_values(validated_data)
        if podcast is None:
            return
        try:
            podcast, season = resolve_canonical_episode_owner(
                podcast=podcast,
                season=season,
            )
        except DjangoValidationError as exc:
            detail = getattr(exc, "message_dict", None) or {"podcast": exc.messages}
            raise serializers.ValidationError(detail) from exc
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"podcast": "The canonical ownership conflicts with existing Season metadata."}
            ) from exc
        validated_data["podcast"] = podcast
        validated_data["season"] = season

    def create(self, validated_data):
        canonical_write = bool(
            (CANONICAL_EPISODE_ACCESS_FIELDS - {"preview_duration_seconds"}) & validated_data.keys()
        )
        countries = validated_data.pop("countries", [])
        competitions = validated_data.pop("competitions", [])
        regions = validated_data.pop("regions", [])
        teams = validated_data.pop("teams", [])
        players = validated_data.pop("players", [])
        matches = validated_data.pop("matches", [])
        categories = validated_data.pop("categories", [])
        tags = validated_data.pop("tags", None)
        new_images_data = validated_data.pop("new_images", [])

        with transaction.atomic():
            self._resolve_owner(validated_data)
            if tags is not None:
                validated_data["tags"] = _prepare_tags_for_model(self.Meta.model, tags)
            instance = Episode.objects.create(**validated_data)

            if countries:
                instance.countries.set(countries)
            if competitions:
                instance.competitions.set(competitions)
            if regions:
                instance.regions.set(regions)
            if teams:
                instance.teams.set(teams)
            if players:
                instance.players.set(players)
            if matches:
                instance.matches.set(matches)
            if categories:
                instance.categories.set(categories)

            if canonical_write:
                synchronize_episode_legacy_projection(instance)
            else:
                synchronize_episode_access_from_legacy(instance)

            if new_images_data:
                for img_payload in new_images_data:
                    _create_image_for_instance(instance, img_payload)

            return instance

    def update(self, instance, validated_data):
        canonical_write = bool(
            (CANONICAL_EPISODE_ACCESS_FIELDS - {"preview_duration_seconds"}) & validated_data.keys()
        )
        legacy_write = bool(LEGACY_EPISODE_ACCESS_FIELDS & validated_data.keys())
        countries = validated_data.pop("countries", None)
        competitions = validated_data.pop("competitions", None)
        regions = validated_data.pop("regions", None)
        teams = validated_data.pop("teams", None)
        players = validated_data.pop("players", None)
        matches = validated_data.pop("matches", None)
        categories = validated_data.pop("categories", None)
        tags = validated_data.pop("tags", None)

        new_images_data = validated_data.pop("new_images", [])

        with transaction.atomic():
            self._resolve_owner(validated_data)
            if tags is not None:
                instance.tags = _prepare_tags_for_model(self.Meta.model, tags)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if countries is not None:
                instance.countries.set(countries)
            if competitions is not None:
                instance.competitions.set(competitions)
            if regions is not None:
                instance.regions.set(regions)
            if teams is not None:
                instance.teams.set(teams)
            if players is not None:
                instance.players.set(players)
            if matches is not None:
                instance.matches.set(matches)
            if categories is not None:
                instance.categories.set(categories)

            if canonical_write:
                synchronize_episode_legacy_projection(instance)
            elif legacy_write:
                synchronize_episode_access_from_legacy(
                    instance,
                    derive_required_plan=categories is not None,
                )

            if new_images_data:
                for img_payload in new_images_data:
                    _create_image_for_instance(instance, img_payload)

            return instance


class PodcastParentModelSerializer(serializers.ModelSerializer):
    countries = CountrySerializer(many=True, read_only=True)
    competitions = LeagueModelSerializer(many=True, read_only=True)
    regions = RegionSerializer(many=True, read_only=True)
    teams = TeamModelSerializer(many=True, read_only=True)
    players = PlayerSerializer(many=True, read_only=True)
    matches = MatchSerializer(many=True, read_only=True)

    categories = CategorySerializer(many=True, read_only=True)
    image = ImageSerializer(source="get_image_url", read_only=True)

    images = ImageSerializer(
        many=True, read_only=True, source="get_images"
    )  # source calls Image.objects.filter_by_instance

    subscriber_count = serializers.IntegerField(source="subscribers.count", read_only=True)

    class Meta:
        model = Podcast
        fields = [
            "id",
            "title",
            "subtitle",
            "structure",
            "description",
            "slug",
            "parent",
            "status",
            "explicit_content",
            "language",
            "website_url",
            "published_at",
            "tags",
            "categories",
            "images",
            "image",
            "countries",
            "competitions",
            "regions",
            "teams",
            "players",
            "matches",
            "view_count",
            "subscriber_count",
            "timestamp",
            "updated",
        ]


class PodcastModelSerializer(PodcastParentModelSerializer):
    parent = PodcastParentModelSerializer(read_only=True)
    seasons = SeasonSerializer(many=True, read_only=True)

    class Meta(PodcastParentModelSerializer.Meta):
        fields = PodcastParentModelSerializer.Meta.fields + ["parent", "seasons"]


class EpisodeModelSerializer(serializers.ModelSerializer):
    tags = TagsField(render_as_list=True, required=False, allow_null=True)
    hosts = TagsField(render_as_list=True, required=False, allow_null=True)
    audio = AudioSerializer(many=True, read_only=True)

    # analytics M2M
    podcast = PodcastModelSerializer(read_only=True)
    season = SeasonSerializer(read_only=True)
    countries = CountrySerializer(many=True, read_only=True)
    competitions = LeagueModelSerializer(many=True, read_only=True)
    regions = RegionSerializer(many=True, read_only=True)
    teams = TeamModelSerializer(many=True, read_only=True)
    players = PlayerSerializer(
        many=True,
    )
    matches = MatchSerializer(many=True, read_only=True)

    categories = CategorySerializer(many=True, read_only=True)

    images = ImageSerializer(
        many=True, read_only=True, source="get_images"
    )  # source calls Image.objects.filter_by_instance

    class Meta:
        model = Episode
        fields = [
            "id",
            "podcast",
            "season",
            "audio",
            "title",
            "subtitle",
            "description",
            "slug",
            "episode_number",
            "episode_type",
            "explicit_content",
            "duration_seconds",
            "hosts",
            "tags",
            "public_release_date",
            "exclusive",
            "early_access_hours",
            "trend_score",
            "status",
            "visibility",
            "premium_available_at",
            "public_available_at",
            "required_plan",
            "preview_duration_seconds",
            "published_at",
            "view_count",
            "categories",
            "images",
            "countries",
            "competitions",
            "regions",
            "teams",
            "players",
            "matches",
            "timestamp",
            "updated",
        ]
