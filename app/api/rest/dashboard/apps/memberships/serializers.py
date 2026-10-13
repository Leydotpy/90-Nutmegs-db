from typing import Any

from apps.memberships.models import (
    Entitlement,
    Feature,
    Membership,
    Plan,
    PlanFeature,
    Subscription,
)
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from api.rest.dashboard.apps.users.serializers import ClerkUserSerializer


# --- Feature serializers (unchanged) ---
class FeatureCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = [
            "id",
            "kind",
            "slug",
            "description",
            "is_content_feature",
            "early_access_hours",
            "seats_limited",
            "seats",
            "transcription_monthly_minutes",
        ]
        read_only_fields = ("id", "slug")


class FeatureDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = [
            "id",
            "kind",
            "slug",
            "description",
            "is_content_feature",
            "early_access_hours",
            "seats_limited",
            "seats",
            "transcription_monthly_minutes",
            "created",
            "updated",
        ]
        read_only_fields = fields


# --- Plan & PlanFeature (unchanged, keep previous behaviour) ---
class PlanFeatureCreateSerializer(serializers.ModelSerializer):
    feature = serializers.PrimaryKeyRelatedField(queryset=Feature.objects.all(), required=True)

    class Meta:
        model = PlanFeature
        fields = ("id", "plan", "feature", "notes")
        read_only_fields = ("id",)


class PlanFeatureDisplaySerializer(serializers.ModelSerializer):
    feature = FeatureDisplaySerializer(read_only=True)

    class Meta:
        model = PlanFeature
        fields = ("id", "feature", "notes")


class PlanCreateSerializer(serializers.ModelSerializer):
    features = serializers.ListField(child=serializers.JSONField(), required=False)

    class Meta:
        model = Plan
        fields = ("id", "name", "tier", "price_monthly", "price_annual", "features")
        read_only_fields = ("id",)

    def _resolve_or_create_feature(self, feature_payload: Any) -> Feature:
        if isinstance(feature_payload, str):
            return Feature.objects.get(id=feature_payload)
        if isinstance(feature_payload, dict):
            serializer = FeatureCreateSerializer(data=feature_payload)
            serializer.is_valid(raise_exception=True)
            return serializer.save()
        try:
            return Feature.objects.get(pk=feature_payload)
        except Exception as exc:
            raise serializers.ValidationError("Invalid feature reference") from exc

    def create(self, validated_data):
        from django.db import transaction

        features_payload = validated_data.pop("features", [])
        with transaction.atomic():
            plan = Plan.objects.create(**validated_data)
            for fp in features_payload:
                feature = self._resolve_or_create_feature(fp)
                PlanFeature.objects.create(plan=plan, feature=feature)
        return plan

    def update(self, instance, validated_data):
        from django.db import transaction

        features_payload = validated_data.pop("features", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if features_payload is not None:
            with transaction.atomic():
                instance.planfeature_set.all().delete()
                for fp in features_payload:
                    feature = self._resolve_or_create_feature(fp)
                    PlanFeature.objects.create(plan=instance, feature=feature)
        return instance


class PlanDisplaySerializer(serializers.ModelSerializer):
    plan_features = PlanFeatureDisplaySerializer(
        source="planfeature_set", many=True, read_only=True
    )
    features = FeatureDisplaySerializer(many=True, read_only=True)

    class Meta:
        model = Plan
        fields = (
            "id",
            "name",
            "tier",
            "price_monthly",
            "price_annual",
            "features",
            "plan_features",
        )
        read_only_fields = fields


# API representations belong to the API layer, not domain AppConfig.ready().
def _get_serializer_for_content_type(ct: ContentType) -> type[serializers.ModelSerializer] | None:
    from api.rest.dashboard.apps.podcasts.serializers import (
        EpisodeModelSerializer,
        PodcastModelSerializer,
    )

    serializers_by_model = {
        "podcasts.podcast": PodcastModelSerializer,
        "podcasts.episode": EpisodeModelSerializer,
    }
    serializer_cls = serializers_by_model.get(f"{ct.app_label.lower()}.{ct.model.lower()}")
    if serializer_cls:
        return serializer_cls

    return None


# --- Entitlement serializers ---
class EntitlementCreateSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField(write_only=True)
    object_id = serializers.CharField()

    class Meta:
        model = Entitlement
        fields = (
            "id",
            "user",
            "content_type",
            "object_id",
            "granted_by_subscription",
            "granted_at",
            "expires_at",
            "revoked",
            "notes",
        )
        read_only_fields = ("id", "granted_at")

    def _get_content_type(self, val: str) -> ContentType:
        # Accept "app_label.model" or content_type id string
        try:
            if "." in val:
                app_label, model = val.split(".", 1)
                ct = ContentType.objects.get(app_label=app_label, model=model)
            else:
                ct = ContentType.objects.get(pk=val)
            return ct
        except ContentType.DoesNotExist as exc:
            raise serializers.ValidationError({"content_type": "invalid content type"}) from exc

    def validate(self, attrs):
        ct_val = attrs.pop("content_type")
        attrs["content_type"] = self._get_content_type(ct_val)
        return super().validate(attrs)


class EntitlementDisplaySerializer(serializers.ModelSerializer):
    user = ClerkUserSerializer(read_only=True)
    content_type = serializers.SerializerMethodField()
    content_object_data = serializers.SerializerMethodField()
    granted_by_subscription = serializers.PrimaryKeyRelatedField(read_only=True)

    def get_content_type(self, obj):
        return f"{obj.content_type.app_label}.{obj.content_type.model}"

    def get_content_object_data(self, obj):
        serializer_cls = _get_serializer_for_content_type(obj.content_type)
        if serializer_cls is None:
            # Unknown generic targets may contain passwords, keys or private
            # metadata. Do not even fetch them to build a display string.
            return {"id": str(obj.object_id)}
        content = obj.content_object
        if content is None:
            return None
        return serializer_cls(content, context=self.context).data

    class Meta:
        model = Entitlement
        fields = (
            "id",
            "user",
            "content_type",
            "object_id",
            "content_object_data",
            "granted_by_subscription",
            "granted_at",
            "expires_at",
            "revoked",
            "notes",
        )
        read_only_fields = fields


# --- Membership & Subscription serializers (unchanged but kept here) ---
class MembershipSerializer(serializers.ModelSerializer):
    user = ClerkUserSerializer(read_only=True)
    plan = PlanDisplaySerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ("id", "user", "customer_id", "plan")
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    membership = MembershipSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "membership",
            "subscription_id",
            "active",
            "status",
            "start_date",
            "trial_ends",
            "end_date",
            "external_id",
            "auto_renew",
        )
        read_only_fields = fields
