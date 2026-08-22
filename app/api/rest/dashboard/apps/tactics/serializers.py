from django.db import transaction
from rest_framework import serializers

from apps.match.models import Match
from apps.persons.models import Player, Staff
from apps.region.leagues.clubs.models import Team
from apps.tactics.models import (
    LineUp,
    Shape, )
from apps.tactics.models import (
    LineUp as LineUpModel,
    Position,
    Formation,
    TeamLineUp as TeamLineUpModel,
    MatchLineUp as MatchLineUpModel,
)


# --- small read serializers for nested display ---
class PlayerSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ["id", "name", "nickname"]
        read_only_fields = fields


class PositionSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ["id", "position", "top", "left", "bottom", "right"]
        read_only_fields = fields


class FormationSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Formation
        fields = ["id", "name"]
        read_only_fields = fields


# --- line-up entry serializer (input + read) ---
class LineUpEntrySerializer(serializers.Serializer):
    """Accepts player and position ids for creation; returns nested readability on response."""
    id = serializers.IntegerField(required=False)  # optional, if referencing existing LineUp
    player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())
    position = serializers.PrimaryKeyRelatedField(queryset=Position.objects.all())

    def to_representation(self, instance):
        # instance may be a LineUpModel instance (for read)
        if isinstance(instance, LineUpModel):
            return {
                "id": instance.pk,
                "player": PlayerSimpleSerializer(instance.player).data,
                "position": PositionSimpleSerializer(instance.position).data,
            }
        return super().to_representation(instance)


# --- TeamLineUp create/read serializer ---
class TeamLineUpCreateSerializer(serializers.Serializer):
    """
    Create or reference a TeamLineUp.

    Accepts either:
      - id: (existing TeamLineUp pk) OR
      - nested creation:
          team (id),
          formation (id) OR formation_data { shape: shape_id, name: str },
          manager (id, optional),
          lineup: [{player: id, position: id}, ...]
    """
    id = serializers.IntegerField(required=False)
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(), required=False)
    formation = serializers.PrimaryKeyRelatedField(queryset=Formation.objects.all(), required=False, allow_null=True)
    formation_data = serializers.DictField(required=False)  # {"shape": uuid/int, "name": "Custom"}
    manager = serializers.PrimaryKeyRelatedField(queryset=Staff.objects.all(), required=False, allow_null=True)
    lineup = LineUpEntrySerializer(many=True, required=False)

    def validate(self, attrs):
        # If id provided, ensure nothing else (or allow mix?) — we'll prefer id-only or nested.
        if "id" in attrs:
            # if id supplied, ignore nested creation fields
            return attrs

        # require team and formation or formation_data
        if "team" not in attrs:
            raise serializers.ValidationError("When creating a TeamLineUp you must supply 'team'.")

        if ("formation" not in attrs) and ("formation_data" not in attrs):
            raise serializers.ValidationError(
                "Provide either existing 'formation' id or 'formation_data' to create one.")

        # validate lineup players belong to team
        team = attrs.get("team")
        lineup = attrs.get("lineup", [])
        for entry in lineup:
            player = entry["player"]
            if player.team is None or team is None:
                # if team or player team is null, allow but warn? we'll raise
                raise serializers.ValidationError(
                    f"Player {player} must belong to a team and match provided team {team}.")
            if str(player.team.pk) != str(team.pk):
                raise serializers.ValidationError(f"Player {player} does not belong to team {team}.")

        # If formation is provided and lineup contains positions, ensure all positions belong to formation.shape
        formation = attrs.get("formation")
        if formation is not None and lineup:
            shape = formation.shape
            for entry in lineup:
                position = entry["position"]
                if position.shape_id != shape.id:
                    raise serializers.ValidationError(
                        f"Position {position} does not belong to formation shape {shape}."
                    )

        return attrs

    def create(self, validated_data):
        # If id provided, just return the existing TeamLineUp
        if validated_data.get("id"):
            return TeamLineUpModel.objects.get(pk=validated_data["id"])

        team = validated_data["team"]
        formation = validated_data.get("formation")
        formation_data = validated_data.get("formation_data")
        manager = validated_data.get("manager", None)
        lineup_entries = validated_data.get("lineup", [])

        # If formation_data provided, create a Formation instance
        if formation is None and formation_data:
            # formation_data should include 'shape' and optional 'name'
            shape_id = formation_data.get("shape")
            name = formation_data.get("name", "custom")
            if not shape_id:
                raise serializers.ValidationError("formation_data must include 'shape' id.")
            # lazy import to avoid cycles
            from apps.tactics.models import Shape
            shape = Shape.objects.get(pk=shape_id)
            formation = Formation.objects.create(shape=shape, name=name)

        # create the TeamLineUp pointing to formation
        team_lineup = TeamLineUpModel.objects.create(
            team=team,
            lineup=formation,
            manager=manager
        )

        # create LineUp instances and associate them to formation (formation.lineup M2M)
        created_lineups = []
        for entry in lineup_entries:
            player = entry["player"]
            position = entry["position"]
            lu = LineUpModel.objects.create(player=player, position=position)
            # attach to formation's lineup list
            # formation may be shared; if you want to keep formation templates separate,
            # consider making a fresh Formation copy per TeamLineUp (we created one if formation_data was used)
            formation.lineup.add(lu)
            created_lineups.append(lu)

        return team_lineup


# read serializer for TeamLineUp (nested detailed)
class LineUpDetailSerializer(serializers.ModelSerializer):
    player = PlayerSimpleSerializer(read_only=True)
    position = PositionSimpleSerializer(read_only=True)

    class Meta:
        model = LineUpModel
        fields = ["id", "player", "position"]


class TeamLineUpSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(read_only=True)
    manager = serializers.PrimaryKeyRelatedField(read_only=True)
    formation = FormationSimpleSerializer(read_only=True)
    lineup = LineUpDetailSerializer(many=True, source="lineup_set", read_only=True)

    class Meta:
        model = TeamLineUpModel
        fields = ["id", "team", "formation", "manager", "lineup"]


# --- MatchLineUp serializer ---
class MatchLineUpSerializer(serializers.ModelSerializer):
    match = serializers.PrimaryKeyRelatedField(queryset=Match.objects.all())
    home_lineup = TeamLineUpSerializer(read_only=True)
    away_lineup = TeamLineUpSerializer(read_only=True)

    # provide write support by accepting nested TeamLineUpCreateSerializer payloads
    home_lineup_data = TeamLineUpCreateSerializer(write_only=True, required=False)
    away_lineup_data = TeamLineUpCreateSerializer(write_only=True, required=False)

    class Meta:
        model = MatchLineUpModel
        fields = ["id", "match", "home_lineup", "away_lineup", "home_lineup_data", "away_lineup_data"]
        read_only_fields = ["id", "home_lineup", "away_lineup"]

    def validate(self, attrs):
        # basic verification is done in the viewset when binding to a Match
        return attrs

    def create(self, validated_data):
        # We do not create here normally — MatchViewSet action will call TeamLineUpCreateSerializer directly
        raise NotImplementedError(
            "Use MatchViewSet.match_lineups action to create lineups for a match."
        )


class PositionSerializer(serializers.ModelSerializer):
    shape = serializers.PrimaryKeyRelatedField(queryset=Shape.objects.all())

    class Meta:
        model = Position
        fields = ["id", "position", "top", "left", "bottom", "right", "timestamp", "updated", "shape"]
        read_only_fields = ["id", "timestamp", "updated"]


class LineUpSerializer(serializers.ModelSerializer):
    player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())
    position = PositionSerializer()

    class Meta:
        model = LineUp
        fields = ["id", "player", "position"]

    def create(self, validated_data):
        position_data = validated_data.pop("position")
        pos_serializer = PositionSerializer(data=position_data)
        pos_serializer.is_valid(raise_exception=True)
        position = pos_serializer.save()
        return LineUp.objects.create(position=position, **validated_data)

    def update(self, instance, validated_data):
        position_data = validated_data.pop("position", None)
        if position_data:
            PositionSerializer().update(instance.position, position_data)
        instance.player = validated_data.get("player", instance.player)
        instance.save()
        return instance


class ShapeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shape
        fields = ["id", "name", "style"]


class FormationSerializer(serializers.ModelSerializer):
    shape = serializers.PrimaryKeyRelatedField(queryset=Shape.objects.all())
    lineup = LineUpSerializer(many=True, required=False)

    class Meta:
        model = Formation
        fields = ["id", "shape", "lineup"]

    def create(self, validated_data):
        lineup_data = validated_data.pop("lineup", [])
        with transaction.atomic():
            formation = Formation.objects.create(**validated_data)
            for lu in lineup_data:
                lu["player"] = Player.objects.get(pk=lu["player"]) if isinstance(lu["player"], (str, int)) else lu[
                    "player"]
                line_serializer = LineUpSerializer(data=lu)
                line_serializer.is_valid(raise_exception=True)
                lineup_obj = line_serializer.save()
                formation.lineup.add(lineup_obj)
            return formation
