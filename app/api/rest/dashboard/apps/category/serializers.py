from apps.category.models import Category
from rest_framework import serializers


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "slug", "tier", "weight", "created_at"]
        read_only_fields = ["id", "slug", "tier", "created_at"]
