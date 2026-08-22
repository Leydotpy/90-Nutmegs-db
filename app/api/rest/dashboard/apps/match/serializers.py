from django.db import transaction
from rest_framework import serializers

from apps.match.models import (
    Match, Event, Goal, Shot, Foul,
    SetPiece, Substitution, Booking, Possession, TeamPossession, GoalEvent, FoulEvent
)
from apps.persons.models import (
    Player, )
from apps.region.leagues.clubs.models import Team, Stadium
from apps.region.leagues.models import League, Campaign


class ShotSerializer(serializers.ModelSerializer):
    player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())

    class Meta:
        model = Shot
        fields = ["id", "team", "player", "is_on_target", "minute"]
        read_only_fields = ["id", "minute"]


class FoulSerializer(serializers.ModelSerializer):
    player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())

    class Meta:
        model = Foul
        fields = ["id", "team", "player", "minute"]
        read_only_fields = ["id", "minute"]


class SetPieceSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())

    class Meta:
        model = SetPiece
        fields = ["id", "team", "type", "minute"]
        read_only_fields = ["id", "minute"]


class GoalSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    scorer = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())
    assist = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all(), allow_null=True, required=False)
    is_own_goal = serializers.BooleanField(default=False)

    class Meta:
        model = Goal
        fields = ["id", "team", "scorer", "assist", "minute", "is_own_goal"]
        read_only_fields = ["id", "minute"]

    def validate(self, attrs):
        if attrs.get("assist") and attrs.get("scorer") and attrs["assist"].team != attrs["scorer"].team:
            raise serializers.ValidationError("Goal scorer and assist provider must be teammates.")
        return attrs

    def create(self, validated_data):
        goal = super().create(validated_data)

        # Attach to match event
        match = self.context["match"]
        GoalEvent.objects.create(
            event=match.event,
            goal=goal
        )

        return goal


class TeamPossessionSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())

    class Meta:
        model = TeamPossession
        fields = ["id", "team", "possession"]
        read_only_fields = ["id"]


class PossessionSerializer(serializers.ModelSerializer):
    home = TeamPossessionSerializer()
    away = TeamPossessionSerializer()

    class Meta:
        model = Possession
        fields = ["id", "home", "away"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        home_data = validated_data.pop("home")
        away_data = validated_data.pop("away")
        with transaction.atomic():
            home = TeamPossession.objects.create(**home_data)
            away = TeamPossession.objects.create(**away_data)
            poss = Possession.objects.create(home=home, away=away)
            return poss


class EventSerializer(serializers.ModelSerializer):
    # Accept nested lists of already created objects (ids) or nested objects (dicts)
    bookings = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    substitutions = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)
    shots = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)
    set_piece = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)
    fouls = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)
    goals = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)
    possession = PossessionSerializer(required=False)

    class Meta:
        model = Event
        fields = [
            "id", "match", "bookings", "substitutions", "possession", "shots",
            "set_piece", "fouls", "goals"
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        bookings_ids = validated_data.pop("bookings", [])
        substitutions_data = validated_data.pop("substitutions", [])
        shots_data = validated_data.pop("shots", [])
        set_piece_data = validated_data.pop("set_piece", [])
        fouls_data = validated_data.pop("fouls", [])
        goals_data = validated_data.pop("goals", [])
        possession_data = validated_data.pop("possession", None)

        with transaction.atomic():
            if possession_data:
                possession = PossessionSerializer().create(possession_data)
                validated_data["possession"] = possession
            event = Event.objects.create(**validated_data)

            if bookings_ids:
                bookings_qs = Booking.objects.filter(pk__in=bookings_ids)
                event.bookings.add(*bookings_qs)

            # create substitutions
            created_subs = []
            for s in substitutions_data:
                sub = Substitution.objects.create(**s)
                created_subs.append(sub)
            if created_subs:
                event.substitutions.add(*created_subs)

            # shots
            created_shots = [Shot.objects.create(**s) for s in shots_data]
            if created_shots:
                event.shots.add(*created_shots)

            # set_piece
            created_setpieces = [SetPiece.objects.create(**s) for s in set_piece_data]
            if created_setpieces:
                event.set_piece.add(*created_setpieces)

            # fouls
            created_fouls = [Foul.objects.create(**f) for f in fouls_data]
            for f in created_fouls:
                # link through FoulEvent
                FoulEvent.objects.create(event=event, foul=f)
            # goals
            created_goals = []
            for g in goals_data:
                goal_serializer = GoalSerializer(data=g)
                goal_serializer.is_valid(raise_exception=True)
                goal = goal_serializer.save()
                created_goals.append(goal)
                GoalEvent.objects.create(event=event, goal=goal)

            return event

    def update(self, instance, validated_data):
        # This updater will be conservative: only update possession if provided; append lists
        bookings_ids = validated_data.pop("bookings", None)
        substitutions_data = validated_data.pop("substitutions", None)
        shots_data = validated_data.pop("shots", None)
        set_piece_data = validated_data.pop("set_piece", None)
        fouls_data = validated_data.pop("fouls", None)
        goals_data = validated_data.pop("goals", None)
        possession_data = validated_data.pop("possession", None)

        with transaction.atomic():
            if possession_data is not None:
                # replace possession with new one
                if hasattr(instance, "possession") and instance.possession:
                    # naive replace: create new TeamPossession rows and Possession
                    instance.possession.home.delete()
                    instance.possession.away.delete()
                    instance.possession.delete()
                instance.possession = PossessionSerializer().create(possession_data)
                instance.save()

            if bookings_ids is not None:
                qs = Booking.objects.filter(pk__in=bookings_ids)
                instance.bookings.add(*qs)

            if substitutions_data is not None:
                created_subs = [Substitution.objects.create(**s) for s in substitutions_data]
                instance.substitutions.add(*created_subs)

            if shots_data is not None:
                created_shots = [Shot.objects.create(**s) for s in shots_data]
                instance.shots.add(*created_shots)

            if set_piece_data is not None:
                created_sp = [SetPiece.objects.create(**s) for s in set_piece_data]
                instance.set_piece.add(*created_sp)

            if fouls_data is not None:
                created_fouls = [Foul.objects.create(**f) for f in fouls_data]
                for f in created_fouls:
                    FoulEvent.objects.create(event=instance, foul=f)

            if goals_data is not None:
                for g in goals_data:
                    gs = GoalSerializer(data=g)
                    gs.is_valid(raise_exception=True)
                    goal = gs.save()
                    GoalEvent.objects.create(event=instance, goal=goal)

            return instance


class MatchSerializer(serializers.ModelSerializer):
    home_team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    away_team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    venue = serializers.PrimaryKeyRelatedField(queryset=Stadium.objects.all(), allow_null=True, required=False)
    competition = serializers.PrimaryKeyRelatedField(queryset=League.objects.all())
    campaign = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.all())
    event = EventSerializer(read_only=True)
    # convenience read-only fields for counts
    home_scores_count = serializers.IntegerField(read_only=True)
    away_scores_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Match
        fields = [
            "id", "home_team", "away_team", "venue", "day", "date", "competition",
            "campaign", "home_scores_count", "away_scores_count", "event"
        ]
        read_only_fields = ["id", "home_scores_count", "away_scores_count", "event"]

    def validate(self, attrs):
        if attrs["home_team"] == attrs["away_team"]:
            raise serializers.ValidationError(
                "Home team and away team must be different."
            )
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            return Match.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        with transaction.atomic():
            instance.save()
            return instance


class ShotCreateSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())

    class Meta:
        model = Shot
        fields = ["id", "team", "player", "is_on_target"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        team = attrs["team"]
        player = attrs["player"]
        if player.team != team:
            raise serializers.ValidationError("Player must belong to the provided team.")
        return attrs

    def create(self, validated_data):
        shot = Shot.objects.create(**validated_data)
        # attach to match.event in view (context must pass event)
        return shot


class FoulCreateSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())

    class Meta:
        model = Foul
        fields = ["id", "team", "player"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs["player"].team != attrs["team"]:
            raise serializers.ValidationError("Player must belong to the provided team.")
        return attrs

    def create(self, validated_data):
        return Foul.objects.create(**validated_data)


class SetPieceCreateSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())

    class Meta:
        model = SetPiece
        fields = ["id", "team", "type"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        return SetPiece.objects.create(**validated_data)


class BookingCreateSerializer(serializers.ModelSerializer):
    player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    booking = serializers.ChoiceField(choices=Booking.Type.choices)

    class Meta:
        model = Booking
        fields = ["id", "player", "team", "booking", "is_straight_red", "is_second_yellow"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs["player"].team != attrs["team"]:
            raise serializers.ValidationError("Player must belong to the provided team.")
        return attrs


class SubstitutionCreateSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    player_out = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())
    player_in = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())
    reason = serializers.ChoiceField(choices=Substitution.Reason.choices)

    class Meta:
        model = Substitution
        fields = ["id", "team", "player_out", "player_in", "minute", "reason"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs["player_out"].team != attrs["team"]:
            raise serializers.ValidationError("player_out must belong to the provided team.")
        if attrs["player_in"].team != attrs["team"]:
            raise serializers.ValidationError("player_in must belong to the provided team.")
        if attrs["player_out"] == attrs["player_in"]:
            raise serializers.ValidationError("player_out and player_in must be different.")
        return attrs

    def create(self, validated_data):
        return Substitution.objects.create(**validated_data)


class GoalCreateSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    scorer = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all())
    assist = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all(), allow_null=True, required=False)
    is_own_goal = serializers.BooleanField(default=False)

    class Meta:
        model = Goal
        fields = ["id", "team", "scorer", "assist", "is_own_goal"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        scorer = attrs["scorer"]
        team = attrs["team"]
        assist = attrs.get("assist")
        if scorer.team != team:
            raise serializers.ValidationError("Scorer must belong to the provided team.")
        if assist and assist.team != team:
            raise serializers.ValidationError("Assist must belong to the same team as the scorer.")
        return attrs

    def create(self, validated_data):
        return Goal.objects.create(**validated_data)


#
# Timeline item serializer: normalize different event models into a single shape
#
class TimelineItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.CharField()
    minute = serializers.IntegerField(allow_null=True)
    team = serializers.CharField(allow_null=True)
    player = serializers.CharField(allow_null=True)
    payload = serializers.DictField()
