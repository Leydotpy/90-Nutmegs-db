from api.rest.dashboard.audit import StaffAuditMixin
from api.rest.dashboard.permissions import StaffReadOnlyOrSuperuser
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, SAFE_METHODS, BasePermission
from rest_framework.response import Response

from apps.memberships.models import Feature, Plan, PlanFeature, Entitlement, Membership, Subscription
from core.compat import get_user_model
from .serializers import (
    FeatureCreateSerializer,
    FeatureDisplaySerializer,
    PlanCreateSerializer,
    PlanDisplaySerializer,
    PlanFeatureCreateSerializer,
    PlanFeatureDisplaySerializer,
    EntitlementCreateSerializer,
    EntitlementDisplaySerializer,
    MembershipSerializer,
    SubscriptionSerializer,
)

User = get_user_model()


# --- FeatureViewSet (unchanged) ---
class FeatureViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    queryset = Feature.objects.all().order_by("kind")

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return FeatureDisplaySerializer
        return FeatureCreateSerializer

    permission_classes = (StaffReadOnlyOrSuperuser,)


# --- PlanViewSet: unchanged except added prefetch and same permission pattern ---
class PlanViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    queryset = Plan.objects.prefetch_related("features", "planfeature_set__feature").all()

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return PlanDisplaySerializer
        return PlanCreateSerializer

    permission_classes = (StaffReadOnlyOrSuperuser,)

    @action(detail=True, methods=["post"], permission_classes=(StaffReadOnlyOrSuperuser,))
    def add_feature(self, request, pk=None):
        plan = self.get_object()
        serializer = PlanFeatureCreateSerializer(data={**request.data, "plan": plan.id})
        serializer.is_valid(raise_exception=True)
        feature_data = request.data.get("feature")
        if isinstance(feature_data, dict):
            fser = FeatureCreateSerializer(data=feature_data)
            fser.is_valid(raise_exception=True)
            feature = fser.save()
        else:
            feature = get_object_or_404(Feature, pk=feature_data)
        with transaction.atomic():
            pf, created = PlanFeature.objects.get_or_create(plan=plan, feature=feature,
                                                            defaults={"notes": request.data.get("notes", "")})
            if not created:
                notes = request.data.get("notes")
                if notes:
                    pf.notes = notes
                    pf.save(update_fields=["notes"])
        return Response(PlanFeatureDisplaySerializer(pf).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class PlanFeatureViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    queryset = PlanFeature.objects.select_related("plan", "feature").all()

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return PlanFeatureDisplaySerializer
        return PlanFeatureCreateSerializer

    permission_classes = (StaffReadOnlyOrSuperuser,)


class EntitlementViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    queryset = Entitlement.objects.select_related("user", "granted_by_subscription", "content_type").all()

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return EntitlementDisplaySerializer
        return EntitlementCreateSerializer

    permission_classes = (StaffReadOnlyOrSuperuser,)


# -------------------------
# Membership & Subscription
# -------------------------
class MembershipViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    """
    Admin-level control over memberships. Read access for staff, create/update/destroy only for superusers.
    Basic server-side validation applied on create/update.
    """
    queryset = Membership.objects.select_related("user", "plan").all()
    serializer_class = MembershipSerializer
    permission_classes = (StaffReadOnlyOrSuperuser,)

    def perform_create(self, serializer):
        # Validate: user exists and doesn't already have a membership (OneToOne enforces this but we provide clear error)
        user = serializer.validated_data.get("user") or serializer.initial_data.get("user")
        plan = serializer.validated_data.get("plan") or serializer.initial_data.get("plan")
        if user is None:
            raise serializers.ValidationError({"user": "User must be provided"})
        # note: OneToOneField on Membership will raise IntegrityError on duplicate, but check early
        if Membership.objects.filter(user=user).exists():
            raise serializers.ValidationError({"user": "This user already has a membership"})
        # ensure plan exists (it will be enforced by FK but explicit check helps)
        if plan is None:
            raise serializers.ValidationError({"plan": "Plan must be provided"})
        serializer.save()

    def perform_update(self, serializer):
        # Prevent changing `user` to a user who already has membership
        user = serializer.validated_data.get("user")
        if user and Membership.objects.exclude(pk=serializer.instance.pk).filter(user=user).exists():
            raise serializers.ValidationError({"user": "Another membership already exists for this user"})
        serializer.save()


class SubscriptionViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    """
    Admin-only create/update/destroy (superusers), staff can read.
    Basic server-side validation:
      - membership must exist
      - end_date (if provided) must be >= start_date
    """
    queryset = Subscription.objects.select_related("membership").all()
    serializer_class = SubscriptionSerializer
    permission_classes = (StaffReadOnlyOrSuperuser,)

    def validate_dates(self, data):
        start = data.get("start_date")
        end = data.get("end_date")
        trial = data.get("trial_ends")
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "end_date cannot be before start_date"})
        if trial and start and trial < start:
            raise serializers.ValidationError({"trial_ends": "trial_ends cannot be before start_date"})

    def perform_create(self, serializer):
        data = serializer.validated_data
        # Ensure membership exists
        membership = data.get("membership") or serializer.initial_data.get("membership")
        if membership is None:
            raise serializers.ValidationError({"membership": "Membership is required"})
        self.validate_dates(data)
        serializer.save()

    def perform_update(self, serializer):
        data = serializer.validated_data
        self.validate_dates(data)
        serializer.save()
