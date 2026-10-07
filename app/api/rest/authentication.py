"""Authentication adapters that are safe during Django app population."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from redis.exceptions import RedisError
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import APIException, AuthenticationFailed


class AuthenticationServiceUnavailable(APIException):
    """Fail a bearer request closed when its verification cache is unavailable."""

    status_code = 503
    default_detail = "Authentication service is temporarily unavailable."
    default_code = "authentication_service_unavailable"


class ClerkBearerAuthentication(BaseAuthentication):
    """Load the Clerk SDK authenticator only when a request is evaluated.

    The SDK imports Django user models at module import time. DRF may resolve
    authentication classes while legacy API AppConfigs are still populating,
    so referencing the SDK class directly raises ``AppRegistryNotReady``.
    """

    def authenticate(self, request):
        authorization = get_authorization_header(request).split()

        # Clerk's resolver accepts ``__session*`` cookies as credentials. That
        # is appropriate for Clerk's middleware, but not for a DRF
        # BaseAuthentication implementation because DRF exempts its own
        # authentication path from Django's CSRF middleware. Only delegate an
        # explicit bearer credential here; returning None preserves the
        # SessionAuthentication fallback and its CSRF enforcement.
        if not authorization or authorization[0].lower() != b"bearer":
            return None
        if len(authorization) == 1:
            raise AuthenticationFailed(
                "Invalid Authorization header. No bearer token provided."
            )
        if len(authorization) > 2:
            raise AuthenticationFailed(
                "Invalid Authorization header. Bearer token must not contain spaces."
            )
        try:
            authorization[1].decode("utf-8")
        except UnicodeError as exc:
            raise AuthenticationFailed("Invalid Authorization header.") from exc

        from django_clerk_sdk.core.auth.clerk.service import (
            USER_INACTIVE,
            resolve_clerk_auth,
        )

        try:
            result = resolve_clerk_auth(request)
        except RedisError as exc:
            raise AuthenticationServiceUnavailable() from exc

        if result.is_authenticated:
            return result.user, result.token
        if not result.has_credentials:
            # A syntactically valid bearer header was present before the SDK
            # was called. Never let an SDK result downgrade that explicit
            # authentication attempt into cookie/session fallback.
            raise AuthenticationFailed("Invalid or expired Clerk token.")

        # The SDK returns a RequestState for an ordinary rejected token. Its
        # broad provider exception path instead returns a token/hash but no
        # state and places the internal exception string in ``reason``. Do not
        # expose that string or misclassify the outage as bad credentials.
        if (
            getattr(result, "token", None)
            and getattr(result, "state", None) is None
            and getattr(result, "reason", None) != USER_INACTIVE
        ):
            raise AuthenticationServiceUnavailable()
        raise AuthenticationFailed("Invalid or expired Clerk token.")

    def authenticate_header(self, request):
        return "Bearer"


class ClerkBearerAuthenticationScheme(OpenApiAuthenticationExtension):
    """Describe the lazy Clerk adapter as the HTTP bearer scheme it wraps."""

    target_class = "api.rest.authentication.ClerkBearerAuthentication"
    name = "clerkBearerAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
