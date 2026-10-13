"""Verified Clerk identity -> the existing local user, without email relinking."""

import hashlib
import logging
import time
from dataclasses import dataclass
from types import SimpleNamespace

from clerk_backend_api.security.types import AuthErrorReason, TokenVerificationErrorReason
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction
from django_clerk_sdk.core.auth.clerk.sdk import clerk_client

logger = logging.getLogger(__name__)
USER_INACTIVE = "user-inactive"
SERVICE_UNAVAILABLE = "identity-service-unavailable"
_SERVICE_FAILURE_REASONS = frozenset(
    {
        AuthErrorReason.SECRET_KEY_MISSING,
        TokenVerificationErrorReason.SECRET_KEY_MISSING,
        TokenVerificationErrorReason.JWK_FAILED_TO_LOAD,
        TokenVerificationErrorReason.JWK_REMOTE_INVALID,
        TokenVerificationErrorReason.JWK_FAILED_TO_RESOLVE,
        TokenVerificationErrorReason.SERVER_ERROR,
    }
)


class IdentityConflict(Exception):
    """An existing account requires explicit operator reconciliation."""


@dataclass
class AuthenticationResult:
    user: object
    has_credentials: bool
    token: str | None = None
    state: object = None
    reason: str | None = None

    @property
    def is_authenticated(self):
        return bool(self.user.is_authenticated)


def user_for_verified_identity(subject):
    """Only call after verifying the token; never match users by email/claims."""
    user_model = get_user_model()
    existing = user_model.objects.filter(clerk_user_id=subject).first()
    if existing is not None:
        return existing

    profile = clerk_client.get_user_details(subject)
    if getattr(profile, "id", None) != subject or getattr(profile, "banned", False):
        raise IdentityConflict()
    email = None
    for address in getattr(profile, "email_addresses", ()) or ():
        if (
            getattr(address, "id", None) == getattr(profile, "primary_email_address_id", None)
            and getattr(getattr(address, "verification", None), "status", None) == "verified"
        ):
            email = address.email_address.strip() or None
            break
    try:
        with transaction.atomic():
            # Unique Clerk ID is the final concurrency guard. Re-check after the
            # provider lookup so parallel first requests converge on one row.
            existing = user_model.objects.filter(clerk_user_id=subject).first()
            if existing is not None:
                return existing
            if email and user_model.objects.filter(email__iexact=email).exists():
                raise IdentityConflict()
            user = user_model(
                clerk_user_id=subject,
                username="clerk_" + hashlib.sha256(subject.encode()).hexdigest(),
                email=email,
                first_name=(getattr(profile, "first_name", "") or "")[:255],
                last_name=(getattr(profile, "last_name", "") or "")[:255],
                is_active=True,
                is_staff=False,
                is_superuser=False,
            )
            user.set_unusable_password()
            user.save(force_insert=True)
            return user
    except IntegrityError:
        # Only the same external identity may win a concurrent insert. An email
        # or username conflict must never select or rewrite another account.
        existing = user_model.objects.filter(clerk_user_id=subject).first()
        if existing is None:
            raise IdentityConflict() from None
        return existing


def resolve_clerk_auth(request):
    django_request = getattr(request, "_request", request)
    cached = getattr(django_request, "_sanfootball_identity_result", None)
    if cached is not None:
        return cached
    authorization = django_request.headers.get("Authorization", "").split()
    token = None
    malformed = False
    if authorization and authorization[0].lower() == "bearer":
        malformed = len(authorization) != 2
        token = authorization[1] if not malformed else None
    elif not authorization:
        # Preserve the SDK's browser-cookie compatibility. DRF session auth
        # enforces CSRF when these credentials are used for unsafe methods.
        token = next(
            (
                value
                for name, value in django_request.COOKIES.items()
                if name.startswith("__session")
            ),
            None,
        )
    result = AuthenticationResult(AnonymousUser(), bool(token or malformed), token=token)
    if token and not malformed:
        try:
            # Verify on EVERY request: no token->user cache can outlive exp/nbf.
            # Pass the credential already selected above. The pinned SDK's
            # header parser only recognizes literal "Bearer ", whereas HTTP
            # authentication schemes are case-insensitive. This also prevents
            # cookie parsing differences from changing which token is verified.
            state = clerk_client.authenticate_request(
                SimpleNamespace(headers={"Authorization": f"Bearer {token}"})
            )
            result.state = state
            if state.reason in _SERVICE_FAILURE_REASONS:
                result.reason = SERVICE_UNAVAILABLE
                logger.warning("Identity verification service unavailable")
            payload = state.payload or {}
            subject = payload.get("sub")
            expiry = payload.get("exp")
            if (
                state.is_signed_in
                and isinstance(subject, str)
                and 0 < len(subject) <= 255
                and isinstance(expiry, (int, float))
                and expiry > time.time()
            ):
                user = user_for_verified_identity(subject)
                if user.is_active:
                    result.user = user
                else:
                    result.reason = USER_INACTIVE
        except IdentityConflict:
            result.reason = "identity-conflict"
            logger.warning("Identity mapping rejected: account reconciliation required")
        except Exception:
            # Neither provider errors nor credentials enter logs/responses.
            result.state = None
            result.reason = SERVICE_UNAVAILABLE
            logger.warning("Identity verification service unavailable")
    django_request._sanfootball_identity_result = result
    return result
