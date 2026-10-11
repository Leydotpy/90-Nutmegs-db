from unittest import mock

from django.db import DatabaseError
from django.test import TestCase


class HealthEndpointTests(TestCase):
    def test_liveness_is_dependency_free(self):
        response = self.client.get("/health/live/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "90Nutmegs"})

    def test_readiness_checks_database(self):
        response = self.client.get("/health/ready/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["checks"],
            {"database": "ok", "cache": "ok"},
        )

    @mock.patch("conf.health.connection.cursor", side_effect=DatabaseError("offline"))
    def test_readiness_fails_closed_without_leaking_error(self, _cursor):
        response = self.client.get("/health/ready/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {
                "status": "unavailable",
                "checks": {"database": "error", "cache": "ok"},
            },
        )

    @mock.patch("conf.health.cache.set", side_effect=ConnectionError("offline"))
    def test_readiness_reports_cache_failure_without_details(self, _cache_set):
        response = self.client.get("/health/ready/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {
                "status": "unavailable",
                "checks": {"database": "ok", "cache": "error"},
            },
        )
        self.assertNotIn("offline", response.content.decode())
