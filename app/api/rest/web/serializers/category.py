from rest_framework import serializers

from api.rest.web.serializers.membership import PlanModelSerializer
from apps.category.models import Category

class CategorySerializer(serializers.ModelSerializer):
    tier = PlanModelSerializer(read_only=True)
    class Meta:
        model = Category
        fields = "__all__"