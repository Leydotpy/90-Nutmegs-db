from rest_framework import serializers

from api.rest.dashboard.apps.media.images.serializers import ImageSerializer
from api.rest.web.serializers.media import ImageModelSerializer
from apps.region.models import Region, Country
from apps.region.leagues.models import League
from apps.region.leagues.clubs.models import Team


# --- Region serializers -----------------------------------------------------
class RegionSerializer(serializers.ModelSerializer):
    image = ImageSerializer(read_only=True)
    class Meta:
        model = Region
        fields = ["id", "name", "code", "slug", "timestamp", "image"]
        read_only_fields = ["id", "slug", "timestamp", "image"]


# --- Country serializers ----------------------------------------------------
class CountrySerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    image = ImageSerializer(read_only=True)

    class Meta:
        model = Country
        fields = ["id", "region", "name", "slug", "code", "image", "timestamp"]
        read_only_fields = ["id", "slug", "timestamp"]


class CountryCreateSerializer(serializers.ModelSerializer):
    """
    Used when creating a country under a Region action - region passed implicitly by view.
    """
    class Meta:
        model = Country
        fields = ["id", "name", "code"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        # The view will provide .context["region"] (Region instance)
        region = self.context.get("region")
        if region is None:
            raise serializers.ValidationError("Region context missing.")
        return Country.objects.create(region=region, **validated_data)


class CountryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["name", "code"]


# --- League serializers -----------------------------------------------------
class LeagueSerializer(serializers.ModelSerializer):
    # 'region' here maps to Country model (legacy naming in League model)
    region = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), allow_null=True, required=False)

    class Meta:
        model = League
        fields = ["id", "region", "name", "short_name", "slug", "code", "timestamp", "popularity"]
        read_only_fields = ["id", "slug", "timestamp"]


class LeagueModelSerializer(serializers.ModelSerializer):
    # 'region' here maps to Country model (legacy naming in League model)
    region = CountrySerializer(read_only=True)
    image = ImageModelSerializer(read_only=True)

    class Meta:
        model = League
        fields = ["id", "region", "name", "short_name", "slug", "code", "timestamp", "popularity", "image"]
        read_only_fields = ["id", "slug", "timestamp", "image", "region"]


class LeagueCreateSerializer(serializers.ModelSerializer):
    """
    Create a League for a Country. The view will validate that the country belongs to the Region.
    Accepts:
      - region (country id)
      - name (required)
    """
    # region = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())

    class Meta:
        model = League
        fields = ["name", "short_name", "code", "popularity"]

    def create(self, validated_data):
        return League.objects.create(**validated_data)


class LeagueUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = ["name", "short_name", "code", "popularity"]

    def validate(self, attrs):
        popularity = attrs.get("popularity", 0)
        if popularity > 5:
            raise serializers.ValidationError(detail={"popularity": "Popularity must be a score of 1 to 5"})
        return attrs



# --- Team serializers -------------------------------------------------------
class TeamSerializer(serializers.ModelSerializer):
    league = serializers.PrimaryKeyRelatedField(queryset=League.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Team
        fields = ["id", "league", "name", "short_name", "code", "slug", "popularity", "timestamp"]
        read_only_fields = ["id", "slug", "timestamp"]


class TeamModelSerializer(serializers.ModelSerializer):
    league = LeagueModelSerializer(required=False, read_only=True)
    image = ImageModelSerializer(read_only=True)

    class Meta:
        model = Team
        fields = ["id", "league", "name", "image", "short_name", "code", "slug", "popularity", "timestamp"]
        read_only_fields = ["id", "slug", "timestamp", "league", "image"]



class TeamCreateSerializer(serializers.ModelSerializer):
    # league = serializers.PrimaryKeyRelatedField(queryset=League.objects.all(), required=True)

    class Meta:
        model = Team
        fields = ["name", "short_name", "code", "popularity"]

    def create(self, validated_data):
        return Team.objects.create(**validated_data)


class TeamUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["name", "short_name", "code", "popularity"]
