"""Routed dashboard access, commercial override and atomic audit guarantees."""

from unittest.mock import patch

from apps.memberships.models import Feature, Plan, PlanFeature
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import URLPattern, get_resolver
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate


def dashboard_callbacks(patterns, prefix=""):
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if isinstance(pattern, URLPattern):
            if route.startswith("api/rest/dashboard/") and "callbacks/giffy/" not in route:
                yield route, pattern.callback
        else:
            yield from dashboard_callbacks(pattern.url_patterns, route)


class StaffAuthorizationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.client = APIClient()
        self.user = get_user_model().objects.create(username="staff-policy-listener")
        self.staff = get_user_model().objects.create(username="content-staff", is_staff=True)
        self.admin = get_user_model().objects.create(
            username="commerce-admin", is_staff=True, is_superuser=True
        )

    def test_every_dashboard_route_rejects_anonymous_listener_and_inactive_staff(self):
        inactive = get_user_model().objects.create(
            username="inactive-staff", is_staff=True, is_active=False
        )
        factory = APIRequestFactory()
        count = 0
        for route, callback in dashboard_callbacks(get_resolver().url_patterns):
            actions = getattr(callback, "actions", None)
            method = next(iter(actions)) if actions else "get"
            for user in (None, self.user, inactive):
                with self.subTest(route=route, user=getattr(user, "username", "anonymous")):
                    request = getattr(factory, method)("/staff-permission-probe/")
                    if user:
                        force_authenticate(request, user=user)
                    response = callback(request)
                    self.assertIn(response.status_code, (401, 403))
            count += 1
        self.assertGreater(count, 100)
        self.assertFalse(LogEntry.objects.exists())

    def test_content_staff_can_read_but_cannot_mutate_commerce_even_nested_action(self):
        plan = Plan.objects.create(name="Existing plan")
        feature = Feature.objects.create(kind=Feature.Kind.DOWNLOADABLE)
        self.client.force_authenticate(self.staff)
        self.assertEqual(
            self.client.get("/api/rest/dashboard/apps/memberships/plans/").status_code, 200
        )
        self.assertEqual(
            self.client.post(
                "/api/rest/dashboard/apps/memberships/plans/", {"name": "Denied"}
            ).status_code,
            403,
        )
        response = self.client.post(
            f"/api/rest/dashboard/apps/memberships/plans/{plan.pk}/add_feature/",
            {"feature": str(feature.pk)},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(PlanFeature.objects.exists())
        self.assertFalse(LogEntry.objects.exists())

    def test_successful_commercial_create_and_delete_are_audited_without_payload(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/rest/dashboard/apps/memberships/features/",
            {"kind": Feature.Kind.DOWNLOADABLE, "description": "Private commercial label"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        feature = Feature.objects.get()
        entry = LogEntry.objects.get()
        self.assertEqual(entry.user_id, self.admin.pk)
        self.assertEqual(entry.object_id, str(feature.pk))
        self.assertEqual(entry.content_type.model_class(), Feature)
        self.assertNotIn(feature.description, entry.change_message + entry.object_repr)
        self.assertIn('"action": "create"', entry.change_message)
        response = self.client.delete(
            f"/api/rest/dashboard/apps/memberships/features/{feature.pk}/"
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(LogEntry.objects.count(), 2)

    def test_audit_failure_rolls_back_commercial_mutation(self):
        self.client.force_authenticate(self.admin)
        with (
            patch(
                "api.rest.dashboard.audit.LogEntry.objects.create",
                side_effect=RuntimeError("audit unavailable"),
            ),
            self.assertRaisesMessage(RuntimeError, "audit unavailable"),
        ):
            self.client.post(
                "/api/rest/dashboard/apps/memberships/features/",
                {"kind": Feature.Kind.DOWNLOADABLE},
            )
        self.assertFalse(Feature.objects.exists())

    def test_unsigned_provider_callback_is_still_denied(self):
        self.assertEqual(
            self.client.post(
                "/api/rest/dashboard/apps/promotions/callbacks/giffy/", {}, format="json"
            ).status_code,
            403,
        )
