from django.contrib.auth import get_user_model
from django.test import SimpleTestCase

from api.rest.web.serializers.auth import UserDisplaySerializer


class UserDisplaySerializerTests(SimpleTestCase):
    def test_serializes_only_public_display_fields(self):
        user = get_user_model()(
            id=42,
            clerk_user_id="user_private_provider_identifier",
            email="private@example.com",
            username="ada",
            first_name="Ada",
            last_name="Lovelace",
            image="https://images.example.test/ada.png",
            password="pbkdf2_sha256$private-password-hash",
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )

        data = UserDisplaySerializer(user).data

        self.assertEqual(
            set(data),
            {
                "id",
                "username",
                "first_name",
                "last_name",
                "image",
                "fullname",
                "name",
            },
        )
        self.assertEqual(data["id"], 42)
        self.assertEqual(data["username"], "ada")
        self.assertEqual(data["fullname"], "Ada Lovelace")

    def test_does_not_expose_identity_auth_or_activity_fields(self):
        user = get_user_model()(
            clerk_user_id="user_private_provider_identifier",
            email="private@example.com",
            username="listener",
            password="pbkdf2_sha256$private-password-hash",
            is_staff=True,
            is_superuser=True,
        )

        data = UserDisplaySerializer(user).data

        sensitive_fields = {
            "password",
            "clerk_user_id",
            "email",
            "last_login",
            "is_superuser",
            "is_staff",
            "is_active",
            "date_joined",
            "last_active_at",
            "groups",
            "user_permissions",
        }
        self.assertTrue(sensitive_fields.isdisjoint(data))
