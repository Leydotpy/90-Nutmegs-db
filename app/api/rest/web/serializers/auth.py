from rest_framework import serializers

from django_clerk_sdk.core.compat import get_user_model


User = get_user_model()



class UserDisplaySerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(source="get_full_name")
    name = serializers.CharField(source="get_short_name")
    class Meta:
        model = User
        fields = "__all__"