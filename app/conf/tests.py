"""Characterization tests for settings selection and startup safety."""

from __future__ import annotations

import ast
import base64
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)

APP_DIR = Path(__file__).resolve().parent.parent
TEST_STREAM_PRIVATE_KEY_B64 = base64.b64encode(
    rsa.generate_private_key(public_exponent=65_537, key_size=2048).private_bytes(
        Encoding.PEM,
        PrivateFormat.PKCS8,
        NoEncryption(),
    )
).decode("ascii")

REQUIRED_PRODUCTION_ENV = {
    "DJANGO_SECRET_KEY": (
        "production-test-secret-not-for-deployment-with-more-than-fifty-characters"
    ),
    "DJANGO_ALLOWED_HOSTS": "example.test",
    "DATABASE_URL": "postgresql://sanfootball:password@db.example.test/sanfootball",
    "REDIS_URL": "redis://127.0.0.1:6379/1",
    "CELERY_BROKER_URL": "redis://127.0.0.1:6379/2",
    "CLERK_SECRET_KEY": "production-test-clerk-secret",
    "CLERK_AUTH_PARTIES": "https://app.example.test",
    "GIFFY_SHARED_SECRET": ("production-test-giffy-secret-with-at-least-thirty-two-characters"),
    "MAIN_PUBLIC_BASE_URL": "https://api.example.test",
    "GIFFY_API_BASE_URL": "https://giffy.example.test",
    "CLOUDFLARE_ACCOUNT_ID": "test-account",
    "CLOUDFLARE_API_TOKEN": "test-api-token",
    "R2_ACCESS_KEY_ID": "test-r2-access",
    "R2_SECRET_ACCESS_KEY": "test-r2-secret",
    "R2_PRIVATE_BUCKET_NAME": "test-private-media",
    "R2_PUBLIC_BUCKET_NAME": "test-public-media",
    "MEDIA_FILEFIELD_R2_CUTOVER_CONFIRMED": "true",
    "R2_PUBLIC_BASE_URL": "https://media.example.test",
    "CLOUDFLARE_IMAGES_ACCOUNT_HASH": "test-images-hash",
    "CLOUDFLARE_IMAGES_SIGNING_KEY": "test-images-signing-key",
    "CLOUDFLARE_STREAM_CUSTOMER_CODE": "test-stream-code",
    "CLOUDFLARE_STREAM_SIGNING_KEY_ID": "test-stream-key",
    "CLOUDFLARE_STREAM_SIGNING_PRIVATE_KEY_B64": TEST_STREAM_PRIVATE_KEY_B64,
    "CLOUDFLARE_STREAM_WEBHOOK_SECRET": "test-stream-webhook-secret",
    "MEDIA_UPLOAD_ALLOWED_ORIGINS": "https://app.example.test",
    "CLOUDFLARE_STREAM_ALLOWED_ORIGINS": "app.example.test",
}

# Set these explicitly in child processes so a developer's shell or local
# ``.env`` cannot make a supposedly isolated settings test pass by accident.
EXTERNAL_SERVICE_ENV = {
    "USE_REDIS_CACHE",
    "OPENAI_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_STORAGE_BUCKET_NAME",
    "CLOUDFRONT_DOMAIN",
    "CLOUDFRONT_COOKIE_DOMAIN",
    "CLOUDFRONT_KEY_PAIR_ID",
    "CLOUDFRONT_PRIVATE_KEY",
    "CLOUDFRONT_COOKIE_TTL",
    "CLOUDFRONT_SIGN_CACHE_TIMEOUT_MARGIN",
}

SETTINGS_PROBE = r"""
import json

import django

django.setup()

from django.conf import settings
from django.core.cache import cache

cache.set("settings-startup-probe", "ok", timeout=5)
assert cache.get("settings-startup-probe") == "ok"

print(json.dumps({
    "cache_backend": settings.CACHES["default"]["BACKEND"],
    "database_engine": settings.DATABASES["default"]["ENGINE"],
    "clerk_secret": settings.CLERK_SECRET_KEY,
    "openai_key": settings.OPENAI_API_KEY,
    "aws_access_key": settings.AWS_ACCESS_KEY_ID,
    "media_bucket": settings.MEDIA_BUCKET,
    "celery_broker": settings.CELERY_BROKER_URL,
}))
"""


class SettingsImportTests(unittest.TestCase):
    maxDiff = None

    def _environment(
        self,
        settings_module: str,
        overrides: dict[str, str] | None = None,
    ) -> dict[str, str]:
        environment = os.environ.copy()
        for name in REQUIRED_PRODUCTION_ENV.keys() | EXTERNAL_SERVICE_ENV:
            environment.pop(name, None)
        environment.update({name: "" for name in EXTERNAL_SERVICE_ENV})
        environment.update(
            {
                "USE_REDIS_CACHE": "0",
                "CLOUDFRONT_COOKIE_TTL": "900",
                "CLOUDFRONT_SIGN_CACHE_TIMEOUT_MARGIN": "60",
            }
        )

        environment.update(
            {
                "DJANGO_SETTINGS_MODULE": settings_module,
                "PYTHONPATH": os.pathsep.join(
                    filter(
                        None,
                        (str(APP_DIR), environment.get("PYTHONPATH", "")),
                    )
                ),
            }
        )
        if overrides:
            environment.update(overrides)
        return environment

    def _run_production_import(
        self,
        overrides: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        values = REQUIRED_PRODUCTION_ENV.copy()
        if overrides:
            values.update(overrides)
        return subprocess.run(
            [
                sys.executable,
                "-c",
                "import importlib; importlib.import_module('conf.settings.production')",
            ],
            cwd=APP_DIR,
            env=self._environment("conf.settings.production", values),
            capture_output=True,
            text=True,
            timeout=30,
        )

    def _run_settings_probe(self, settings_module: str) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-c", SETTINGS_PROBE],
            cwd=APP_DIR,
            env=self._environment(
                settings_module,
                {
                    "USE_REDIS_CACHE": "0",
                    "CLERK_SECRET_KEY": "",
                    "OPENAI_API_KEY": "",
                    "AWS_ACCESS_KEY_ID": "",
                    "AWS_SECRET_ACCESS_KEY": "",
                    "AWS_STORAGE_BUCKET_NAME": "",
                    "CLOUDFRONT_KEY_PAIR_ID": "",
                    "CLOUDFRONT_PRIVATE_KEY": "",
                },
            ),
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )
        return json.loads(completed.stdout.strip().splitlines()[-1])

    def test_development_settings_start_without_external_services(self):
        values = self._run_settings_probe("conf.settings.development")

        self.assertEqual(
            values["cache_backend"],
            "django.core.cache.backends.locmem.LocMemCache",
        )
        self.assertEqual(values["database_engine"], "django.db.backends.sqlite3")
        self.assertEqual(values["clerk_secret"], "")
        self.assertEqual(values["openai_key"], "")
        self.assertEqual(values["aws_access_key"], "")
        self.assertEqual(values["media_bucket"], "")

    def test_test_settings_start_without_external_services(self):
        values = self._run_settings_probe("conf.settings.test")

        self.assertEqual(
            values["cache_backend"],
            "django.core.cache.backends.locmem.LocMemCache",
        )
        self.assertEqual(values["database_engine"], "django.db.backends.sqlite3")
        self.assertEqual(values["celery_broker"], "memory://")
        self.assertEqual(values["openai_key"], "")
        self.assertEqual(values["aws_access_key"], "")
        self.assertEqual(values["media_bucket"], "")

    def test_production_rejects_each_missing_required_setting(self):
        script = "import importlib; importlib.import_module('conf.settings.production')"

        for missing_name in REQUIRED_PRODUCTION_ENV:
            with self.subTest(missing_name=missing_name):
                values = REQUIRED_PRODUCTION_ENV.copy()
                values[missing_name] = ""
                completed = subprocess.run(
                    [sys.executable, "-c", script],
                    cwd=APP_DIR,
                    env=self._environment("conf.settings.production", values),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(
                    f"{missing_name} is required by conf.settings.production",
                    completed.stderr,
                )

    def test_production_rejects_non_postgresql_database(self):
        values = REQUIRED_PRODUCTION_ENV.copy()
        values["DATABASE_URL"] = "sqlite:///:memory:"

        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "import importlib; importlib.import_module('conf.settings.production')",
            ],
            cwd=APP_DIR,
            env=self._environment("conf.settings.production", values),
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "DATABASE_URL must use PostgreSQL in conf.settings.production",
            completed.stderr,
        )

    def test_production_rejects_short_secret_key(self):
        values = REQUIRED_PRODUCTION_ENV.copy()
        values["DJANGO_SECRET_KEY"] = "too-short"

        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "import importlib; importlib.import_module('conf.settings.production')",
            ],
            cwd=APP_DIR,
            env=self._environment("conf.settings.production", values),
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "DJANGO_SECRET_KEY must contain at least 50 characters",
            completed.stderr,
        )

    def test_production_rejects_r2_dev_public_delivery(self):
        completed = self._run_production_import({"R2_PUBLIC_BASE_URL": "https://pub-test.r2.dev"})

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not r2.dev", completed.stderr)

    def test_production_rejects_shared_public_and_private_r2_bucket(self):
        completed = self._run_production_import({"R2_PUBLIC_BUCKET_NAME": "test-private-media"})

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must be different", completed.stderr)

    def test_production_requires_explicit_filefield_cutover_confirmation(self):
        completed = self._run_production_import({"MEDIA_FILEFIELD_R2_CUTOVER_CONFIRMED": "false"})

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "MEDIA_FILEFIELD_R2_CUTOVER_CONFIRMED must be true",
            completed.stderr,
        )

    def test_production_rejects_stream_origin_urls(self):
        completed = self._run_production_import(
            {"CLOUDFLARE_STREAM_ALLOWED_ORIGINS": "https://app.example.test"}
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "entries must be DNS hostnames without a scheme",
            completed.stderr,
        )

    def test_production_rejects_non_cloudflare_media_provider(self):
        completed = self._run_production_import({"MEDIA_STORAGE_PROVIDER": "legacy_s3"})

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "MEDIA_STORAGE_PROVIDER must be 'cloudflare_r2' in production",
            completed.stderr,
        )

    def test_production_uses_private_r2_django_storage(self):
        script = r"""
import importlib

settings = importlib.import_module("conf.settings.production")
default = settings.STORAGES["default"]
assert default["BACKEND"] == "pycflare.django.storage.R2MediaStorage"
assert default["OPTIONS"]["querystring_auth"] is True
assert default["OPTIONS"]["settings"].public_base_url is None
assert default["OPTIONS"]["settings"].bucket_name == "test-private-media"
assert settings.CLOUDFLARE_MEDIA_CONFIG.r2_public_base_url == "https://media.example.test"
assert settings.CLOUDFLARE_MEDIA_CONFIG.r2_public_bucket_name == "test-public-media"
"""
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=APP_DIR,
            env=self._environment(
                "conf.settings.production",
                REQUIRED_PRODUCTION_ENV,
            ),
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertEqual(
            completed.returncode,
            0,
            msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )

    def test_production_rejects_delimiter_only_clerk_parties(self):
        completed = self._run_production_import({"CLERK_AUTH_PARTIES": ", ,"})

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "CLERK_AUTH_PARTIES must contain at least one allowed party",
            completed.stderr,
        )

    def test_production_rejects_delimiter_only_allowed_hosts(self):
        completed = self._run_production_import({"DJANGO_ALLOWED_HOSTS": ", ,"})

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "DJANGO_ALLOWED_HOSTS must contain at least one allowed host",
            completed.stderr,
        )

    def test_production_rejects_global_allowed_hosts_wildcard(self):
        completed = self._run_production_import({"DJANGO_ALLOWED_HOSTS": "*"})

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "DJANGO_ALLOWED_HOSTS cannot contain the global '*' wildcard in production",
            completed.stderr,
        )

    def test_production_rejects_partial_signed_hls_configuration(self):
        completed = self._run_production_import({"CLOUDFRONT_DOMAIN": "media.example.test"})

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Signed HLS configuration is incomplete", completed.stderr)
        self.assertIn("CLOUDFRONT_COOKIE_DOMAIN", completed.stderr)

    def test_production_rejects_unrelated_hls_delivery_host(self):
        completed = self._run_production_import(
            {
                "DJANGO_ALLOWED_HOSTS": "api.example.test",
                "CLOUDFRONT_DOMAIN": "d111111abcdef8.cloudfront.net",
                "CLOUDFRONT_COOKIE_DOMAIN": "example.test",
                "CLOUDFRONT_KEY_PAIR_ID": "test-key",
                "CLOUDFRONT_PRIVATE_KEY": "test-private-key",
            }
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "CLOUDFRONT_DOMAIN must equal or be a subdomain of CLOUDFRONT_COOKIE_DOMAIN",
            completed.stderr,
        )

    def test_production_rejects_api_host_outside_hls_cookie_domain(self):
        completed = self._run_production_import(
            {
                "DJANGO_ALLOWED_HOSTS": "api.other.test",
                "CLOUDFRONT_DOMAIN": "media.example.test",
                "CLOUDFRONT_COOKIE_DOMAIN": "example.test",
                "CLOUDFRONT_KEY_PAIR_ID": "test-key",
                "CLOUDFRONT_PRIVATE_KEY": "test-private-key",
            }
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "DJANGO_ALLOWED_HOSTS must include a concrete API hostname that can "
            "set CLOUDFRONT_COOKIE_DOMAIN",
            completed.stderr,
        )

    def test_production_rejects_mixed_concrete_and_wildcard_hls_hosts(self):
        completed = self._run_production_import(
            {
                "DJANGO_ALLOWED_HOSTS": "api.example.test,.example.test",
                "CLOUDFRONT_DOMAIN": "media.example.test",
                "CLOUDFRONT_COOKIE_DOMAIN": "example.test",
                "CLOUDFRONT_KEY_PAIR_ID": "test-key",
                "CLOUDFRONT_PRIVATE_KEY": "test-private-key",
            }
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "Signed HLS requires DJANGO_ALLOWED_HOSTS to contain only concrete "
            "hostnames (no wildcards)",
            completed.stderr,
        )

    def test_production_rejects_wildcard_as_only_hls_api_host(self):
        completed = self._run_production_import(
            {
                "DJANGO_ALLOWED_HOSTS": ".example.test",
                "CLOUDFRONT_DOMAIN": "media.example.test",
                "CLOUDFRONT_COOKIE_DOMAIN": "example.test",
                "CLOUDFRONT_KEY_PAIR_ID": "test-key",
                "CLOUDFRONT_PRIVATE_KEY": "test-private-key",
            }
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "Signed HLS requires DJANGO_ALLOWED_HOSTS to contain only concrete "
            "hostnames (no wildcards)",
            completed.stderr,
        )

    def test_production_accepts_explicit_shared_hls_cookie_domain(self):
        completed = self._run_production_import(
            {
                "DJANGO_ALLOWED_HOSTS": "api.example.test",
                "CLOUDFRONT_DOMAIN": "media.example.test",
                "CLOUDFRONT_COOKIE_DOMAIN": ".example.test",
                "CLOUDFRONT_KEY_PAIR_ID": "test-key",
                "CLOUDFRONT_PRIVATE_KEY": "test-private-key",
            }
        )

        self.assertEqual(
            completed.returncode,
            0,
            msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )

    def test_explicit_production_import_does_not_load_development_shim(self):
        script = r"""
import importlib
import sys
import warnings

with warnings.catch_warnings(record=True) as captured:
    warnings.simplefilter("always")
    importlib.import_module("conf.settings.production")

assert "conf.settings.development" not in sys.modules
assert not any(
    "conf.settings is a deprecated development-only compatibility module"
    in str(item.message)
    for item in captured
)
"""
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=APP_DIR,
            env=self._environment(
                "conf.settings.production",
                REQUIRED_PRODUCTION_ENV,
            ),
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertEqual(
            completed.returncode,
            0,
            msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )

    def test_exact_legacy_settings_selector_retains_development_shim(self):
        script = r"""
import importlib
import sys
import warnings

with warnings.catch_warnings(record=True) as captured:
    warnings.simplefilter("always")
    importlib.import_module("conf.settings")

assert "conf.settings.development" in sys.modules
assert any(
    "conf.settings is a deprecated development-only compatibility module"
    in str(item.message)
    for item in captured
)
"""
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=APP_DIR,
            env=self._environment("conf.settings"),
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertEqual(
            completed.returncode,
            0,
            msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )

    def test_production_http_liveness_probe_is_not_redirected(self):
        values = REQUIRED_PRODUCTION_ENV.copy()
        values["DJANGO_ALLOWED_HOSTS"] = "testserver"
        script = (
            "import django; django.setup(); "
            "from django.test import Client; "
            "response = Client().get('/health/live/'); "
            "assert response.status_code == 200, response.status_code"
        )

        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=APP_DIR,
            env=self._environment("conf.settings.production", values),
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertEqual(
            completed.returncode,
            0,
            msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )


class EntrypointSettingsTests(unittest.TestCase):
    def _settings_defaults(self, relative_path: str) -> list[str]:
        source = (APP_DIR / relative_path).read_text(encoding="utf-8")
        tree = ast.parse(source)
        defaults = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "setdefault" or len(node.args) < 2:
                continue
            first_argument = node.args[0]
            second_argument = node.args[1]
            if (
                isinstance(first_argument, ast.Constant)
                and first_argument.value == "DJANGO_SETTINGS_MODULE"
                and isinstance(second_argument, ast.Constant)
            ):
                defaults.append(second_argument.value)
        return defaults

    def test_command_entrypoint_defaults_to_development(self):
        self.assertEqual(
            self._settings_defaults("manage.py"),
            ["conf.settings.development"],
        )

    def test_deployed_entrypoints_default_to_production(self):
        for relative_path in ("conf/asgi.py", "conf/wsgi.py", "conf/celery.py"):
            with self.subTest(relative_path=relative_path):
                self.assertEqual(
                    self._settings_defaults(relative_path),
                    ["conf.settings.production"],
                )


if __name__ == "__main__":
    unittest.main()
