"""Local mapping and the real SDK signature/time/audience verification boundary."""

import time
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from clerk_backend_api.security.authenticaterequest import authenticate_request
from clerk_backend_api.security.types import (
    AuthenticateRequestOptions,
    AuthStatus,
    RequestState,
    TokenVerificationErrorReason,
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.middleware.csrf import get_token
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIClient

from .identity import IdentityConflict, resolve_clerk_auth, user_for_verified_identity


class IdentityMappingTests(TestCase):
    def profile(self, subject="user_new", email="new@example.test"):
        return SimpleNamespace(
            id=subject,
            first_name="Listener",
            last_name="One",
            banned=False,
            primary_email_address_id="email1",
            email_addresses=[
                SimpleNamespace(
                    id="email1",
                    email_address=email,
                    verification=SimpleNamespace(status="verified"),
                )
            ],
            public_metadata={"is_staff": True, "is_superuser": True, "plan": "insider"},
        )

    @patch("apps.accounts.identity.clerk_client.get_user_details")
    def test_repeat_identity_reuses_one_row_without_claim_privileges(self, details):
        details.return_value = self.profile()
        first = user_for_verified_identity("user_new")
        second = user_for_verified_identity("user_new")
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(get_user_model().objects.filter(clerk_user_id="user_new").count(), 1)
        self.assertFalse(first.is_staff)
        self.assertFalse(first.is_superuser)
        self.assertFalse(first.has_usable_password())
        details.assert_called_once_with("user_new")

    @patch("apps.accounts.identity.clerk_client.get_user_details")
    def test_shared_email_does_not_relink_local_or_external_accounts(self, details):
        original = get_user_model().objects.create(username="original", email="same@example.test")
        details.return_value = self.profile(email="SAME@example.test")
        with self.assertRaises(IdentityConflict):
            user_for_verified_identity("user_new")
        original.refresh_from_db()
        self.assertIsNone(original.clerk_user_id)
        original.clerk_user_id = "different-external-id"
        original.save()
        with self.assertRaises(IdentityConflict):
            user_for_verified_identity("user_new")
        original.refresh_from_db()
        self.assertEqual(original.clerk_user_id, "different-external-id")

    @patch("apps.accounts.identity.clerk_client.get_user_details")
    def test_provider_subject_mismatch_cannot_create_identity(self, details):
        details.return_value = self.profile(subject="another-user")
        with self.assertRaises(IdentityConflict):
            user_for_verified_identity("user_new")
        self.assertFalse(get_user_model().objects.filter(clerk_user_id="user_new").exists())

    @patch("apps.accounts.identity.clerk_client.get_user_details")
    def test_existing_local_suspension_and_staff_state_are_preserved(self, details):
        original = get_user_model().objects.create(
            username="suspended", clerk_user_id="user_suspended", is_active=False, is_staff=True
        )
        result = user_for_verified_identity("user_suspended")
        self.assertEqual(result.pk, original.pk)
        self.assertFalse(result.is_active)
        self.assertTrue(result.is_staff)
        details.assert_not_called()

    def test_external_mapping_is_database_unique_and_local_users_can_remain_unmapped(self):
        user_model = get_user_model()
        user_model.objects.create(username="first", clerk_user_id="same-id")
        with self.assertRaises(IntegrityError), transaction.atomic():
            user_model.objects.create(username="second", clerk_user_id="same-id")
        user_model.objects.create(username="local-one")
        user_model.objects.create(username="local-two")

    @patch("apps.accounts.identity.clerk_client.get_user_details")
    def test_first_login_racing_provider_lookup_converges_on_winner(self, details):
        def concurrent_create(subject):
            get_user_model().objects.create(username="winner", clerk_user_id=subject)
            return self.profile(subject)

        details.side_effect = concurrent_create
        user = user_for_verified_identity("user_new")
        self.assertEqual(user.username, "winner")
        self.assertEqual(get_user_model().objects.filter(clerk_user_id="user_new").count(), 1)


class VerifiedTokenTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public_key = (
            cls.key.public_key()
            .public_bytes(
                serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
            )
            .decode()
        )

    def setUp(self):
        self.user = get_user_model().objects.create(
            username="verified", clerk_user_id="user_verified"
        )
        self.factory = RequestFactory()
        self.options = AuthenticateRequestOptions(
            jwt_key=self.public_key,
            authorized_parties=["https://app.example.test"],
            audience="90nutmegs",
            clock_skew_in_ms=0,
            accepts_token=["session_token"],
        )
        self.verify = patch(
            "apps.accounts.identity.clerk_client.authenticate_request",
            side_effect=lambda request: authenticate_request(request, self.options),
        ).start()
        self.addCleanup(patch.stopall)

    def token(self, **overrides):
        now = int(time.time())
        claims = dict(
            sub="user_verified",
            sid="sess_test",
            iss="https://clerk.example.test",
            azp="https://app.example.test",
            aud="90nutmegs",
            iat=now,
            nbf=now - 1,
            exp=now + 60,
            is_staff=True,
            plan="insider",
        )
        claims.update(overrides)
        return jwt.encode(claims, self.key, algorithm="RS256", headers={"kid": "test-key"})

    def request(self, token):
        return self.factory.get("/api/rest/web/", HTTP_AUTHORIZATION="Bearer " + token)

    def test_valid_signed_identity_uses_one_query_and_ignores_authorization_claims(self):
        with self.assertNumQueries(1):
            result = resolve_clerk_auth(self.request(self.token()))
        self.assertEqual(result.user, self.user)
        self.assertFalse(result.user.is_staff)
        self.assertFalse(result.user.is_superuser)

    def test_invalid_signature_expiry_not_before_audience_and_party_are_rejected(self):
        cases = [
            self.token(exp=int(time.time()) - 60),
            self.token(nbf=int(time.time()) + 60),
            self.token(aud="another-app"),
            self.token(azp="https://attacker.example.test"),
        ]
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cases.append(
            jwt.encode(
                jwt.decode(self.token(), options={"verify_signature": False}),
                other_key,
                algorithm="RS256",
                headers={"kid": "test-key"},
            )
        )
        for token in cases:
            with self.subTest(token_case=cases.index(token)), self.assertNumQueries(0):
                self.assertFalse(resolve_clerk_auth(self.request(token)).is_authenticated)

    def test_each_request_reverifies_and_rechecks_local_suspension(self):
        token = self.token()
        request = self.request(token)
        self.assertTrue(resolve_clerk_auth(request).is_authenticated)
        resolve_clerk_auth(request)
        self.assertEqual(self.verify.call_count, 1)
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.assertFalse(resolve_clerk_auth(self.request(token)).is_authenticated)
        self.assertEqual(self.verify.call_count, 2)

    def test_bearer_scheme_is_case_insensitive_and_takes_precedence_over_cookies(self):
        token = self.token()
        for scheme in ("bearer", "bEaReR", "Bearer"):
            with self.subTest(scheme=scheme):
                request = self.factory.get(
                    "/",
                    HTTP_AUTHORIZATION=f"{scheme} {token}",
                    HTTP_COOKIE="__session=invalid-cookie-token",
                )
                self.assertEqual(resolve_clerk_auth(request).user, self.user)

    @override_settings(ROOT_URLCONF="api.rest.web.serializers.test_authentication")
    def test_verified_cookie_requires_csrf_for_unsafe_requests(self):
        client = APIClient(enforce_csrf_checks=True)
        client.cookies["__session"] = self.token()
        self.assertEqual(client.get("/session-probe/").status_code, 200)
        self.assertEqual(client.post("/session-probe/", {}).status_code, 403)
        csrf_request = self.factory.get("/")
        csrf_token = get_token(csrf_request)
        client.cookies["csrftoken"] = csrf_request.META["CSRF_COOKIE"]
        response = client.post("/session-probe/", {}, HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"username": self.user.username})

    @override_settings(ROOT_URLCONF="api.rest.web.serializers.test_authentication")
    def test_invalid_bearer_cannot_use_valid_cookie_or_django_session(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.user)
        client.cookies["__session"] = self.token()
        response = client.get("/session-probe/", HTTP_AUTHORIZATION="Bearer invalid")
        self.assertEqual(response.status_code, 401)

    @override_settings(ROOT_URLCONF="api.rest.web.serializers.test_authentication")
    def test_jwks_outage_is_unavailable_even_when_sdk_returns_a_state(self):
        self.verify.return_value = RequestState(
            status=AuthStatus.SIGNED_OUT,
            reason=TokenVerificationErrorReason.JWK_FAILED_TO_LOAD,
        )
        self.verify.side_effect = None
        with self.assertLogs("apps.accounts.identity", level="WARNING"):
            response = APIClient().get("/session-probe/", HTTP_AUTHORIZATION="Bearer token")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(), {"detail": "Authentication service is temporarily unavailable."}
        )

    def test_provider_exception_is_not_logged_or_returned(self):
        self.verify.side_effect = RuntimeError("secret-token-value internal-host")
        with self.assertLogs("apps.accounts.identity", level="WARNING") as logs:
            result = resolve_clerk_auth(self.request("token"))
        self.assertFalse(result.is_authenticated)
        self.assertEqual(result.reason, "identity-service-unavailable")
        self.assertNotIn("secret-token-value", str(logs.output))
        self.assertNotIn("internal-host", str(logs.output))
