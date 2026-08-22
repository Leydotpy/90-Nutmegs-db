from typing import Any

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from apps.memberships.models import (
    Entitlement,
    Feature,
    Plan,
    PlanFeature,
    Membership,
    Subscription,
)

from core.compat import get_user_model

from api.rest.dashboard.apps.users.serializers import ClerkUserSerializer

User = get_user_model()


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
        except Exception:
            raise serializers.ValidationError("Invalid feature reference")

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
    plan_features = PlanFeatureDisplaySerializer(source="planfeature_set", many=True, read_only=True)
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


# -------------------------------------------------------------------
# Entitlement nested serialization registry + dynamic fallback
# -------------------------------------------------------------------

# Registry mapping "app_label.model" -> serializer class
ENTITLEMENT_SERIALIZER_REGISTRY: dict[str, type[serializers.ModelSerializer]] = {}

# Example: attempt to register common models automatically (if present).
# If your Episode/Course models live in different apps, register them manually
# (see `register_entitlement_serializer()` below).
try:
    Episode = apps.get_model("episodes", "Episode")


    class EpisodeSerializer(serializers.ModelSerializer):
        class Meta:
            model = Episode
            # choose only sensible fields to avoid huge payloads; adjust as needed
            fields = ("id", "title", "duration", "slug", "published_at")


    ENTITLEMENT_SERIALIZER_REGISTRY["episodes.episode"] = EpisodeSerializer
except LookupError:
    pass

try:
    Course = apps.get_model("courses", "Course")


    class CourseSerializer(serializers.ModelSerializer):
        class Meta:
            model = Course
            fields = ("id", "title", "description", "slug", "published_at")


    ENTITLEMENT_SERIALIZER_REGISTRY["courses.course"] = CourseSerializer
except LookupError:
    pass


def register_entitlement_serializer(app_label: str, model_name: str, serializer_cls: type[serializers.ModelSerializer]):
    """
    Call this in startup (e.g. AppConfig.ready) or at import time to register
    custom serializers for entitlement content objects.

    Example:
        register_entitlement_serializer("podcast", "Episode", MyEpisodeSerializer)
    """
    key = f"{app_label.lower()}.{model_name.lower()}"
    ENTITLEMENT_SERIALIZER_REGISTRY[key] = serializer_cls


def _get_serializer_for_content_type(ct: ContentType) -> type[serializers.ModelSerializer]:
    key = f"{ct.app_label.lower()}.{ct.model.lower()}"
    serializer_cls = ENTITLEMENT_SERIALIZER_REGISTRY.get(key)
    if serializer_cls:
        return serializer_cls

    # fallback: build a simple ModelSerializer that exposes all fields
    class AutoSerializer(serializers.ModelSerializer):
        class Meta:
            model = apps.get_model(ct.app_label, ct.model)
            fields = "__all__"

    return AutoSerializer


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
        except ContentType.DoesNotExist:
            raise serializers.ValidationError({"content_type": "invalid content type"})

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
        try:
            serializer_cls = _get_serializer_for_content_type(obj.content_type)
            serializer = serializer_cls(obj.content_object, context=self.context)
            return serializer.data
        except Exception:
            # fallback to string representation if any step fails
            try:
                return {"display": str(obj.content_object)}
            except Exception:
                return None

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
