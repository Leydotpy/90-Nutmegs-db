from django.db import transaction
from rest_framework import serializers

from api.rest.dashboard.apps.region.serializers import CountrySerializer
from apps.persons.models import (
    Staff, Player, Fitness, Injury, InjuryType, PlayerTransfer, Contract, StaffTransfer
)
from apps.region.leagues.clubs.models import Team
from apps.region.models import Region, Country  # adjust import path as needed


class InjuryTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InjuryType
        fields = ["id", "name", "code"]
        read_only_fields = ["id", "code"]


class InjurySerializer(serializers.ModelSerializer):
    injury = serializers.PrimaryKeyRelatedField(queryset=InjuryType.objects.all())

    class Meta:
        model = Injury
        fields = ["id", "start_date", "return_date", "injury"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        start = attrs.get("start_date") or getattr(self.instance, "start_date", None)
        ret = attrs.get("return_date") or getattr(self.instance, "return_date", None)
        if start and ret and ret < start:
            raise serializers.ValidationError({"return_date": "return_date must be >= start_date"})
        return attrs

    def create(self, validated_data):
        return Injury.objects.create(**validated_data)


class FitnessSerializer(serializers.ModelSerializer):
    # Accept either list of injury dicts, list of injury IDs, or nothing
    injuries = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="List of injuries (dict objects) to create and attach. Each item: {start_date, return_date, injury: <injury_type_id>}"
    )
    injury_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of existing Injury IDs to attach"
    )
    injury_records = InjurySerializer(source="injuries", many=True, read_only=True)

    class Meta:
        model = Fitness
        fields = ["id", "player", "injury_records", "injuries", "injury_ids"]
        read_only_fields = ["id", "injury_records"]

    def create(self, validated_data):
        injuries_data = validated_data.pop("injuries", [])
        injury_ids = validated_data.pop("injury_ids", [])
        player = validated_data.get("player")

        with transaction.atomic():
            fitness = Fitness.objects.create(player=player)
            created = []
            for inj in injuries_data:
                inj_serializer = InjurySerializer(data=inj)
                inj_serializer.is_valid(raise_exception=True)
                created.append(inj_serializer.save())
            if injury_ids:
                qs = Injury.objects.filter(pk__in=injury_ids)
                fitness.injuries.add(*qs)
            if created:
                fitness.injuries.add(*created)
            return fitness

    def update(self, instance, validated_data):
        injuries_data = validated_data.pop("injuries", None)
        injury_ids = validated_data.pop("injury_ids", None)

        with transaction.atomic():
            # Replace injuries if explicit list provided
            if injuries_data is not None:
                instance.injuries.clear()
                created = []
                for inj in injuries_data:
                    inj_serializer = InjurySerializer(data=inj)
                    inj_serializer.is_valid(raise_exception=True)
                    created.append(inj_serializer.save())
                if created:
                    instance.injuries.add(*created)

            # If injury_ids provided, append them (doesn't remove existing)
            if injury_ids is not None:
                qs = Injury.objects.filter(pk__in=injury_ids)
                instance.injuries.add(*qs)

            instance.save()
            return instance


class PlayerSerializer(serializers.ModelSerializer):
    fitness = FitnessSerializer(required=False, read_only=True, allow_null=True)
    nations = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Player
        fields = [
            "id", "nations", "name", "age", "slug", "first_name", "last_name", "middle_name",
            "code", "created", "nickname", "fitness"
        ]
        read_only_fields = ["id", "slug", "created", "fitness", "name", "nickname"]

    def create(self, validated_data):
        with transaction.atomic():
            player = Player.objects.create(**validated_data)
            return player

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        with transaction.atomic():
            instance.save()
            return instance


class StaffSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(), allow_null=True, required=False)
    region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Staff
        fields = ["id", "team", "region", "name", "age", "slug", "code", "created", "job"]
        read_only_fields = ["id", "slug", "created"]


class PlayerModelSerializer(PlayerSerializer):
    nations = CountrySerializer(many=True, read_only=True)

    class Meta(PlayerSerializer.Meta):
        read_only_fields = PlayerSerializer.Meta.read_only_fields + ["nations"]



class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = "__all__"


class PlayerTransferSerializer(serializers.ModelSerializer):
    # player = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all(), allow_null=True, required=True)
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(), allow_null=True, required=True)
    contract = ContractSerializer(required=True)

    class Meta:
        model = PlayerTransfer
        fields = ("id", "team", "fee", "date", "timestamp", "updated", "contract")
        read_only_fields = ("timestamp", "updated", "id")

    def create(self, validated_data):
        contract_data = validated_data.pop("contract")
        with transaction.atomic():
            contract = Contract.objects.create(**contract_data)
            transfer = PlayerTransfer(**validated_data)
            transfer.contract = contract
            transfer.save()
            return transfer

    def update(self, instance: PlayerTransfer, validated_data):
        contract_data = validated_data.pop("contract")
        for attr, val in contract_data.items():
            setattr(instance.contract, attr, val)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        with transaction.atomic():
            instance.contract.save()
            instance.save()
            return instance

