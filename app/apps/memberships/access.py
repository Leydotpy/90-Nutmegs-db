"""Compatibility facade and short-lived cache for canonical access policy."""

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import models
from django.utils import timezone

from .models import Entitlement
from .policies import AccessAction, AccessPolicy, access_policy

try:
    from django_redis import get_redis_connection

    _have_redis = True
except Exception:
    _have_redis = False


CACHE_TTL_SECONDS = getattr(settings, "ACCESS_CACHE_TTL_SECONDS", 30)
USER_CACHE_SET_PREFIX = getattr(settings, "USER_ACCESS_KEY_SET_PREFIX", "user_access_keys")


def get_user_highest_active_subscription(user, *, now=None):
    """Compatibility selector using the policy's transitional state semantics."""

    if not user or not getattr(user, "is_authenticated", False):
        return None
    subscription, _ = AccessPolicy._current_subscription(
        user,
        now or timezone.now(),
    )
    return subscription


def has_entitlement(user, content_obj, *, now=None):
    """Compatibility helper for a valid direct entitlement to an actual object."""

    if not user or not getattr(user, "is_authenticated", False):
        return False
    now = now or timezone.now()
    content_type = ContentType.objects.get_for_model(content_obj)
    return (
        Entitlement.objects.filter(
            user=user,
            content_type=content_type,
            object_id=str(content_obj.pk),
            revoked=False,
        )
        .filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now))
        .exists()
    )


class AccessService:
    """Backwards-compatible Boolean API around :class:`AccessPolicy`.

    New callers should consume ``evaluate`` and its structured decision.  The
    legacy ``has_access`` method remains while serializers/permissions migrate.
    Cache failures are treated as misses and can never create an allow result.
    """

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(
        self,
        cache_backend=cache,
        ttl=CACHE_TTL_SECONDS,
        policy: AccessPolicy | None = None,
    ):
        self.cache = cache_backend
        self.ttl = ttl
        self.policy = policy or access_policy
        self._redis = None
        if _have_redis:
            try:
                self._redis = get_redis_connection("default")
            except NotImplementedError, ValueError:
                self._redis = None

    @staticmethod
    def _cache_key(user, obj, action=AccessAction.STREAM):
        action = AccessAction(action)
        if user and getattr(user, "is_authenticated", False):
            user_key = f"user:{user.pk}"
        else:
            user_key = "user:anon"
        return (
            f"access:{AccessPolicy.VERSION}:{user_key}:"
            f"{obj._meta.label_lower}:{obj.pk}:{action.value}"
        )

    @staticmethod
    def _user_set_key(user):
        return f"{USER_CACHE_SET_PREFIX}:{user.pk}"

    def evaluate(self, *, user, resource, action=AccessAction.STREAM, now=None):
        """Evaluate without making cached state authoritative.

        Explicit ``now`` is passed through for deterministic jobs/tests.  The
        structured decision deliberately is not cached because it contains live
        model instances and expiry metadata.
        """

        return self.policy.evaluate(
            user=user,
            resource=resource,
            action=action,
            now=now,
        )

    def evaluate_media(
        self,
        *,
        user,
        resource,
        variant,
        action=AccessAction.STREAM,
        now=None,
    ):
        """Return an uncached decision bound to one exact canonical media variant."""

        return self.policy.evaluate_media(
            user=user,
            resource=resource,
            variant=variant,
            action=action,
            now=now,
        )

    def has_access(self, user, obj, action=AccessAction.STREAM):
        """Return the legacy Boolean result using an action/version-safe key."""

        action = AccessAction(action)
        key = self._cache_key(user, obj, action)
        try:
            cached = self.cache.get(key)
        except Exception:
            cached = None
        if cached is not None:
            return bool(cached)

        decision = self.evaluate(user=user, resource=obj, action=action)
        try:
            self.cache.set(key, bool(decision.allowed), timeout=self.ttl)
            self._register_cache_key_for_user(user, key)
        except Exception:
            pass
        return decision.allowed

    def invalidate_user_cache(self, user):
        """Clear all cached actions for a user's commercial-state change."""

        self._clear_keys_for_user(user)

    def invalidate_user_obj(self, user, obj):
        """Clear all cached policy actions for one user/resource pair."""

        for action in AccessAction:
            key = self._cache_key(user, obj, action)
            try:
                self.cache.delete(key)
            except Exception:
                pass
            self._unregister_cache_key_for_user(user, key)

    def _register_cache_key_for_user(self, user, key):
        if not user or not getattr(user, "is_authenticated", False):
            return
        if self._redis:
            try:
                self._redis.sadd(self._user_set_key(user), key)
            except Exception:
                pass
            return

        list_key = f"{self._user_set_key(user)}:list"
        existing = self.cache.get(list_key) or []
        if key not in existing:
            existing.append(key)
            self.cache.set(list_key, existing, timeout=self.ttl * 3)

    def _unregister_cache_key_for_user(self, user, key):
        if not user or not getattr(user, "is_authenticated", False):
            return
        if self._redis:
            try:
                self._redis.srem(self._user_set_key(user), key)
            except Exception:
                pass
            return

        list_key = f"{self._user_set_key(user)}:list"
        existing = self.cache.get(list_key) or []
        if key in existing:
            existing.remove(key)
            self.cache.set(list_key, existing, timeout=self.ttl * 3)

    def _get_keys_for_user(self, user):
        if not user or not getattr(user, "is_authenticated", False):
            return []
        if self._redis:
            try:
                keys = self._redis.smembers(self._user_set_key(user))
                return [key.decode() if isinstance(key, bytes) else key for key in keys]
            except Exception:
                return []
        return self.cache.get(f"{self._user_set_key(user)}:list") or []

    def _clear_keys_for_user(self, user):
        for key in self._get_keys_for_user(user):
            try:
                self.cache.delete(key)
            except Exception:
                pass
        if not user or not getattr(user, "is_authenticated", False):
            return
        if self._redis:
            try:
                self._redis.delete(self._user_set_key(user))
            except Exception:
                pass
        else:
            self.cache.delete(f"{self._user_set_key(user)}:list")
