from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from api.rest.web.serializers.membership import PlanModelSerializer
from apps.category.models import Category

@extend_schema_serializer(component_name="PublicCategory")
class CategorySerializer(serializers.ModelSerializer):
    tier = PlanModelSerializer(read_only=True)
    class Meta:
        model = Category
        fields = "__all__"
