from apps.memberships.models import Membership, Plan, Subscription
from rest_framework import serializers

from api.rest.web.serializers.auth import UserDisplaySerializer


class PlanModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ("id", "name", "features", "tier", "price_monthly", "price_annual")


class MembershipSerializer(serializers.ModelSerializer):
    user = UserDisplaySerializer(read_only=True)
    plan = PlanModelSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ("id", "user", "plan")


class SubscriptionSerializer(serializers.ModelSerializer):
    membership = MembershipSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "membership",
            "active",
            "status",
            "start_date",
            "trial_ends",
            "end_date",
            "auto_renew",
        )
