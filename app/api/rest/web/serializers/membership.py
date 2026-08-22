from rest_framework import serializers

from apps.memberships.models import Membership, Plan, Subscription
from api.rest.web.serializers.auth import UserDisplaySerializer


class PlanModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"


class MembershipSerializer(serializers.ModelSerializer):
    user = UserDisplaySerializer(read_only=True)
    plan = PlanModelSerializer(read_only=True)
    class Meta:
        model = Membership
        fields = "__all__"


class SubscriptionSerializer(serializers.ModelSerializer):
    membership = MembershipSerializer(read_only=True)
    class Meta:
        model = Subscription
        fields = "__all__"