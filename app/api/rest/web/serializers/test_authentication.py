from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, modify_settings, override_settings
from django.urls import path
from redis.exceptions import ConnectionError as RedisConnectionError
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView

from api.rest.authentication import (
    AuthenticationServiceUnavailable,
    ClerkBearerAuthentication,
)


class SessionProbeView(APIView):
    authentication_classes = (ClerkBearerAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response({"username": request.user.get_username()})

    def post(self, request):
        return Response({"username": request.user.get_username()})


urlpatterns = [path("session-probe/", SessionProbeView.as_view())]


class ClerkAuthenticationConfigurationTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.authentication = ClerkBearerAuthentication()

    def test_bearer_authentication_precedes_session_compatibility(self):
        classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES

        self.assertIs(classes[0], ClerkBearerAuthentication)
        self.assertEqual(classes[1].__name__, "SessionAuthentication")

    @mock.patch("apps.accounts.identity.resolve_clerk_auth")
    def test_request_without_credentials_falls_through(self, resolve):
        result = self.authentication.authenticate(self.factory.get("/"))

        self.assertIsNone(result)
        resolve.assert_not_called()

    @mock.patch("apps.accounts.identity.resolve_clerk_auth")
    def test_cookie_only_credentials_fall_through_without_clerk_resolution(self, resolve):
        request = self.factory.post(
            "/",
            {"operation": "unsafe"},
            format="json",
            HTTP_COOKIE="__session=attacker-controlled-cookie",
        )

        result = self.authentication.authenticate(request)

        self.assertIsNone(result)
        resolve.assert_not_called()

    @mock.patch("apps.accounts.identity.resolve_clerk_auth")
    def test_explicit_bearer_cannot_downgrade_to_session_fallback(self, resolve):
        resolve.return_value = SimpleNamespace(
            is_authenticated=False,
            has_credentials=False,
            reason=None,
            token=None,
            state=None,
        )
        request = self.factory.get(
            "/",
            HTTP_AUTHORIZATION="Bearer explicit-token",
        )

        with self.assertRaisesMessage(
            AuthenticationFailed,
            "Invalid or expired Clerk token.",
        ):
            self.authentication.authenticate(request)

        resolve.assert_called_once_with(request)

    @mock.patch("apps.accounts.identity.resolve_clerk_auth")
    def test_non_bearer_authorization_falls_through(self, resolve):
        request = self.factory.get(
            "/",
            HTTP_AUTHORIZATION="Basic dXNlcjpwYXNzd29yZA==",
        )

        result = self.authentication.authenticate(request)

        self.assertIsNone(result)
        resolve.assert_not_called()

    @mock.patch("apps.accounts.identity.resolve_clerk_auth")
    def test_malformed_bearer_authorization_fails_before_resolution(self, resolve):
        malformed_headers = (
            "Bearer",
            "Bearer token unexpected-suffix",
        )

        for authorization in malformed_headers:
            with self.subTest(authorization=authorization):
                request = self.factory.get(
                    "/",
                    HTTP_AUTHORIZATION=authorization,
                )
                with self.assertRaises(AuthenticationFailed):
                    self.authentication.authenticate(request)

        resolve.assert_not_called()

    @mock.patch("apps.accounts.identity.resolve_clerk_auth")
    def test_invalid_bearer_credentials_do_not_fall_back_to_session(self, resolve):
        resolve.return_value = SimpleNamespace(
            is_authenticated=False,
            has_credentials=True,
            reason="invalid-token",
            token="invalid",
            state=object(),
        )
        request = self.factory.get("/", HTTP_AUTHORIZATION="Bearer invalid")

        with self.assertRaisesMessage(
            AuthenticationFailed,
            "Invalid or expired Clerk token.",
        ):
            self.authentication.authenticate(request)

    @mock.patch(
        "apps.accounts.identity.resolve_clerk_auth",
        side_effect=RedisConnectionError("cache unavailable"),
    )
    def test_bearer_cache_outage_fails_closed_as_unavailable(self, _authenticate):
        request = self.factory.get("/", HTTP_AUTHORIZATION="Bearer token")

        with self.assertRaises(AuthenticationServiceUnavailable):
            self.authentication.authenticate(request)

    @mock.patch("apps.accounts.identity.resolve_clerk_auth")
    def test_provider_failure_is_sanitized_as_unavailable(self, resolve):
        resolve.return_value = SimpleNamespace(
            is_authenticated=False,
            has_credentials=True,
            reason="provider timeout at internal-host:9000",
            token="token",
            state=None,
        )
        request = self.factory.get("/", HTTP_AUTHORIZATION="Bearer token")

        with self.assertRaisesMessage(
            AuthenticationServiceUnavailable,
            "Authentication service is temporarily unavailable.",
        ) as raised:
            self.authentication.authenticate(request)

        self.assertNotIn("internal-host", str(raised.exception.detail))

    @mock.patch("apps.accounts.identity.resolve_clerk_auth")
    def test_verified_bearer_result_is_delegated(self, resolve):
        user = SimpleNamespace(is_authenticated=True)
        resolve.return_value = SimpleNamespace(
            is_authenticated=True,
            has_credentials=True,
            user=user,
            token="verified-token",
        )

        result = self.authentication.authenticate(
            self.factory.get("/", HTTP_AUTHORIZATION="Bearer verified-token")
        )

        self.assertEqual(result, (user, "verified-token"))


@override_settings(ROOT_URLCONF=__name__)
@modify_settings(
    MIDDLEWARE={
        "remove": "apps.accounts.middleware.ClerkMiddleware",
    }
)
class ClerkSessionCsrfCompatibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            email="listener@example.test",
            username="listener",
            password="not-a-production-password",
            clerk_user_id="user_session_csrf_test",
        )

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_login(self.user)
        self.client.cookies["__session"] = "cookie-only-clerk-token"

    @mock.patch("apps.accounts.identity.resolve_clerk_auth")
    def test_cookie_request_preserves_session_authentication_fallback(self, resolve):
        response = self.client.get("/session-probe/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"username": "listener"})
        resolve.assert_not_called()

    @mock.patch("apps.accounts.identity.resolve_clerk_auth")
    def test_unsafe_cookie_request_is_rejected_by_session_csrf_check(self, resolve):
        response = self.client.post(
            "/session-probe/",
            {"operation": "unsafe"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        resolve.assert_not_called()


@override_settings(ROOT_URLCONF=__name__)
class ClerkMiddlewareCsrfCompatibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            email="clerk-listener@example.test",
            username="clerk-listener",
            password="not-a-production-password",
            clerk_user_id="user_clerk_cookie_csrf_test",
        )

    @mock.patch("apps.accounts.identity.resolve_clerk_auth")
    @mock.patch("apps.accounts.middleware.resolve_clerk_auth")
    def test_clerk_cookie_authenticated_post_still_requires_csrf(
        self,
        middleware_resolve,
        bearer_resolve,
    ):
        middleware_resolve.return_value = SimpleNamespace(user=self.user)
        client = APIClient(enforce_csrf_checks=True)
        client.cookies["__session"] = "cookie-only-clerk-token"

        response = client.post(
            "/session-probe/",
            {"operation": "unsafe"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        middleware_resolve.assert_called_once()
        bearer_resolve.assert_not_called()
