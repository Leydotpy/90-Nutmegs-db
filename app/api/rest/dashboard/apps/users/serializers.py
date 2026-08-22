from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


# --- Clerk User (display-only) ---
class ClerkUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "image", "date_joined")
        read_only_fields = fields
