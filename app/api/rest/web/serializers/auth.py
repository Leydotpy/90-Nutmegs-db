from django_clerk_sdk.core.compat import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserDisplaySerializer(serializers.ModelSerializer):
    """Public, display-only representation of a user.

    Keep this allowlist deliberately small: this serializer is embedded in
    public comments, reactions, and queue responses.
    Authentication identifiers, contact details, permissions, and activity
    metadata must not be exposed through those resources.
    """

    fullname = serializers.CharField(source="get_full_name", read_only=True)
    name = serializers.CharField(source="get_short_name", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "image",
            "fullname",
            "name",
        )
        read_only_fields = fields
