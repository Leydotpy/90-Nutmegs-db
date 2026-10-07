"""OpenAPI quality-gate regression tests."""

from __future__ import annotations

import io
from contextlib import redirect_stderr

from django.test import SimpleTestCase
from drf_spectacular.drainage import reset_generator_stats
from drf_spectacular.generators import SchemaGenerator


class OpenAPISchemaTests(SimpleTestCase):
    def test_schema_generation_emits_no_errors(self):
        """Serializer-less operations must fail tests, not only print errors."""
        diagnostics = io.StringIO()
        reset_generator_stats()

        try:
            with redirect_stderr(diagnostics):
                schema = SchemaGenerator().get_schema(request=None, public=True)
        finally:
            reset_generator_stats()

        error_lines = [
            line for line in diagnostics.getvalue().splitlines() if "Error [" in line
        ]
        self.assertIsNotNone(schema)
        self.assertEqual([], error_lines, diagnostics.getvalue())

        paths = schema["paths"]
        expected_responses = {
            (
                "/api/rest/dashboard/apps/promotions/callbacks/giffy/",
                "post",
            ): {"200", "400", "403", "404"},
            (
                "/api/rest/web/apps/media/offline/devices/register/",
                "post",
            ): {"201", "400"},
            (
                "/api/rest/web/apps/media/offline/licenses/{license_id}/revoke/",
                "post",
            ): {"200", "404"},
            (
                "/api/rest/web/apps/media/offline/packages/request/",
                "post",
            ): {"201", "202", "400", "403", "404"},
            (
                "/api/rest/web/apps/media/offline/packages/status/{task_id}/",
                "get",
            ): {"200"},
            ("/api/rest/web/explore/", "get"): {"200"},
        }
        for (path, method), response_codes in expected_responses.items():
            with self.subTest(path=path, method=method):
                operation = paths[path][method]
                self.assertEqual(response_codes, set(operation["responses"]))
                self.assertIn("content", next(iter(operation["responses"].values())))

        callback_parameters = {
            parameter["name"]
            for parameter in paths[
                "/api/rest/dashboard/apps/promotions/callbacks/giffy/"
            ]["post"]["parameters"]
            if parameter["in"] == "header" and parameter.get("required")
        }
        self.assertEqual(
            {
                "X-SanFootball-Client",
                "X-SanFootball-Timestamp",
                "X-SanFootball-Content-SHA256",
                "X-SanFootball-Signature",
            },
            callback_parameters,
        )

        explore = schema["components"]["schemas"]["ExploreResponse"]
        self.assertEqual(
            {
                "trending",
                "new_releases",
                "editor_picks",
                "top_playlists",
                "recommended",
                "categories",
                "podcasts",
            },
            set(explore["properties"]),
        )
