"""SF-02 configuration failures must be deterministic and value-free."""

import json
import os
import subprocess
import sys
import traceback
import unittest
from unittest import mock

from django.core.exceptions import ImproperlyConfigured

from conf import tests as fixtures
from conf.settings.environment import (
    allowed_hosts,
    config,
    https_origins,
    nonnegative,
    positive,
    service_url,
)


class EnvironmentValidationTests(unittest.TestCase):
    def test_typed_environment_overrides_default_and_can_rotate(self):
        with mock.patch.dict(os.environ, {"SF02_NUMBER": "14"}):
            self.assertEqual(config("SF02_NUMBER", default=1, cast=int), 14)
            os.environ["SF02_NUMBER"] = "15"
            self.assertEqual(config("SF02_NUMBER", default=1, cast=int), 15)

    def test_bad_numeric_environment_never_appears_in_exception_chain(self):
        supplied = "synthetic-private-input-not-a-number"
        with mock.patch.dict(os.environ, {"SF02_NUMBER": supplied}):
            try:
                config("SF02_NUMBER", cast=int)
            except ImproperlyConfigured:
                rendered = traceback.format_exc()
            else:
                self.fail("Invalid numeric configuration was accepted")
        self.assertIn("SF02_NUMBER", rendered)
        self.assertNotIn(supplied, rendered)
        self.assertNotIn("ValueError", rendered)

    def test_hosts_accept_django_host_forms(self):
        hosts = ["api.example.test", ".example.test", "127.0.0.1", "[::1]"]
        self.assertEqual(allowed_hosts(", ".join(hosts)), hosts)

    def test_hosts_reject_urls_ports_and_wildcards(self):
        for value in (
            "",
            ",,",
            "*",
            "*.example.test",
            "https://api.example.test",
            "api.example.test:443",
            "api.example.test/path",
            "api example.test",
            "api\n.example.test",
            "-api.example.test",
            "api..example.test",
        ):
            with self.subTest(value=value), self.assertRaises(ImproperlyConfigured):
                allowed_hosts(value)

    def test_production_origins_are_exact_https_origins(self):
        self.assertEqual(
            https_origins("CORS_ALLOWED_ORIGINS", ["https://app.example.test:443/"]),
            ["https://app.example.test:443"],
        )
        self.assertEqual(https_origins("CORS_ALLOWED_ORIGINS", []), [])

    def test_invalid_origin_errors_do_not_echo_credentials_or_bad_ports(self):
        values = (
            "http://app.example.test",
            "https://*.example.test",
            "*",
            "https://user:origin-sensitive-value@app.example.test",
            "https://app.example.test/path",
            "https://app.example.test?token=private",
            "https://app.example.test#fragment",
            "https://app.example.test:bad-secret",
            "https://app.example.test:0",
            "https://app.example.test:65536",
            "https://app\n.example.test",
            "https://-app.example.test",
        )
        for value in values:
            with self.subTest(value=value):
                with self.assertRaises(ImproperlyConfigured) as raised:
                    https_origins("CSRF_TRUSTED_ORIGINS", [value])
                self.assertIn("CSRF_TRUSTED_ORIGINS", str(raised.exception))
                self.assertNotIn(value, str(raised.exception))

    def test_service_urls_accept_tls_and_private_hostnames(self):
        value = "rediss://worker:synthetic-password@cache.internal:6380/2"
        self.assertEqual(service_url("REDIS_URL", value, ("redis", "rediss")), value)

    def test_service_urls_reject_missing_hosts_and_bad_database_numbers(self):
        for value in (
            "redis:///1",
            "https://cache.test/1",
            "redis://cache:bad-secret/1",
            "redis://cache/-1",
            "redis://cache/not-a-number",
            "redis://*/1",
            "redis://cache:65536/1",
            "redis://cache/1#fragment",
            "redis://cache/1?db=-1",
            "redis://cache/1?db=",
            "redis://cache/1?db=2&db=invalid",
        ):
            with self.subTest(value=value), self.assertRaises(ImproperlyConfigured):
                service_url("REDIS_URL", value, ("redis", "rediss"))

    def test_negative_operational_limits_fail_without_echoing_value(self):
        with self.assertRaisesRegex(ImproperlyConfigured, "LIMIT must be non-negative"):
            nonnegative("LIMIT", -5)
        self.assertEqual(nonnegative("LIMIT", 0), 0)

    def test_service_timeouts_must_be_positive_and_finite(self):
        for value in (0, -1, float("inf"), float("nan")):
            with self.subTest(value=value), self.assertRaises(ImproperlyConfigured):
                positive("TIMEOUT", value)
        self.assertEqual(positive("TIMEOUT", 0.5), 0.5)


class SettingsBoundaryTests(unittest.TestCase):
    def run_probe(self, module, script, overrides=None):
        values = fixtures.REQUIRED_PRODUCTION_ENV.copy() if module.endswith("production") else {}
        # Make security switches deterministic even in an operator's shell.
        values.update(
            {
                "DJANGO_SECRET_KEY_FALLBACKS": "",
                "CORS_ALLOWED_ORIGINS": "",
                "CSRF_TRUSTED_ORIGINS": "",
                "TRUST_PROXY_SSL_HEADER": "false",
                "SECURE_HSTS_SECONDS": "0",
                "SECURE_HSTS_INCLUDE_SUBDOMAINS": "false",
                "SECURE_HSTS_PRELOAD": "false",
                "DATABASE_CONN_MAX_AGE": "60",
            }
        )
        values.update(overrides or {})
        environment = fixtures.SettingsImportTests()._environment(module, values)
        return subprocess.run(
            [sys.executable, "-c", script],
            cwd=fixtures.APP_DIR,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def assert_probe_passes(self, completed):
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_development_honors_explicit_browser_origins(self):
        completed = self.run_probe(
            "conf.settings.development",
            "import json; from django.conf import settings as s; "
            "print(json.dumps([s.CORS_ALLOWED_ORIGINS, s.CSRF_TRUSTED_ORIGINS]))",
            {
                "CORS_ALLOWED_ORIGINS": "http://localhost:4000",
                "CSRF_TRUSTED_ORIGINS": "http://localhost:4000",
            },
        )
        self.assert_probe_passes(completed)
        self.assertEqual(json.loads(completed.stdout), [["http://localhost:4000"]] * 2)

    def test_development_database_errors_omit_credentials(self):
        completed = self.run_probe(
            "conf.settings.development",
            "from django.conf import settings; settings.DATABASES",
            {"DATABASE_URL": "postgresql://user:dsn-sensitive@db:port-sensitive/database"},
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("DATABASE_URL", completed.stderr)
        self.assertNotIn("dsn-sensitive", completed.stderr)
        self.assertNotIn("port-sensitive", completed.stderr)

    def test_test_settings_do_not_inherit_browser_trust_or_callback_secret(self):
        completed = self.run_probe(
            "conf.settings.test",
            "from django.conf import settings as s; "
            "assert s.CORS_ALLOWED_ORIGINS == []; assert s.CSRF_TRUSTED_ORIGINS == []; "
            "assert s.GIFFY_SHARED_SECRET == 'test-giffy-secret'",
            {
                "CORS_ALLOWED_ORIGINS": "https://production.example.test",
                "CSRF_TRUSTED_ORIGINS": "https://production.example.test",
                "GIFFY_SHARED_SECRET": "synthetic-production-secret",
            },
        )
        self.assert_probe_passes(completed)

    def test_local_cookie_settings_support_http_browsers(self):
        for module in ("development", "test"):
            with self.subTest(module=module):
                completed = self.run_probe(
                    f"conf.settings.{module}",
                    "from django.conf import settings as s; "
                    "assert not s.SESSION_COOKIE_SECURE; "
                    "assert not s.RECENTLY_VIEWED_COOKIE_SECURE; "
                    "assert not s.PODCAST_QUEUE_SESSION_COOKIE_SECURE",
                )
                self.assert_probe_passes(completed)

    def test_production_has_closed_browser_defaults_and_explicit_proxy_trust(self):
        completed = self.run_probe(
            "conf.settings.production",
            "from django.conf import settings as s; from django.test import RequestFactory; "
            "assert not s.DEBUG; assert s.SESSION_COOKIE_SECURE and s.CSRF_COOKIE_SECURE; "
            "assert s.RECENTLY_VIEWED_COOKIE_SECURE and s.PODCAST_QUEUE_SESSION_COOKIE_SECURE; "
            "assert s.CORS_ALLOWED_ORIGINS == []; assert s.CSRF_TRUSTED_ORIGINS == []; "
            "assert s.SECURE_PROXY_SSL_HEADER is None; assert s.SECURE_HSTS_SECONDS == 0; "
            "assert not s.SECURE_HSTS_PRELOAD; "
            "assert not RequestFactory().get('/', HTTP_X_FORWARDED_PROTO='https').is_secure()",
            {"DJANGO_DEBUG": "true"},
        )
        self.assert_probe_passes(completed)

    def test_verified_tls_deployment_can_enable_proxy_hsts_and_browser_origins(self):
        completed = self.run_probe(
            "conf.settings.production",
            "from django.conf import settings as s; from django.test import RequestFactory; "
            "assert s.CORS_ALLOWED_ORIGINS == ['https://app.example.test']; "
            "assert s.CSRF_TRUSTED_ORIGINS == ['https://app.example.test']; "
            "assert s.SECURE_HSTS_SECONDS == 31536000 and s.SECURE_HSTS_PRELOAD; "
            "assert RequestFactory().get('/', HTTP_X_FORWARDED_PROTO='https').is_secure()",
            {
                "TRUST_PROXY_SSL_HEADER": "true",
                "SECURE_HSTS_SECONDS": "31536000",
                "SECURE_HSTS_INCLUDE_SUBDOMAINS": "true",
                "SECURE_HSTS_PRELOAD": "true",
                "CORS_ALLOWED_ORIGINS": "https://app.example.test",
                "CSRF_TRUSTED_ORIGINS": "https://app.example.test",
            },
        )
        self.assert_probe_passes(completed)

    def test_production_rejects_malformed_infrastructure_and_trust_settings(self):
        cases = {
            "DATABASE_URL": "postgresql://user:dsn-sensitive@db:port-sensitive/database",
            "REDIS_URL": "redis://cache/not-a-database",
            "CELERY_BROKER_URL": "memory://",
            "DJANGO_ALLOWED_HOSTS": "https://api.example.test",
            "CORS_ALLOWED_ORIGINS": "http://app.example.test",
            "CSRF_TRUSTED_ORIGINS": "https://*.example.test",
            "CLERK_AUTH_PARTIES": "http://app.example.test",
            "GIFFY_API_BASE_URL": "http://localhost:8050",
            "MAIN_PUBLIC_BASE_URL": "https://api.example.test?secret=sensitive",
            "DATABASE_CONN_MAX_AGE": "-1",
            "SECURE_HSTS_SECONDS": "invalid-sensitive-value",
            "R2_PUBLIC_BASE_URL": "https://media.example.test:port-sensitive",
            "MEDIA_UPLOAD_ALLOWED_ORIGINS": "https://app.example.test:port-sensitive",
            "GIFFY_TIMEOUT_SECONDS": "nan",
            "PRESIGN_EXPIRES_SECONDS": "-1",
            "PRESIGN_PREVIEW_EXPIRES_SECONDS": "0",
        }
        for name, value in cases.items():
            with self.subTest(name=name):
                completed = self.run_probe(
                    "conf.settings.production",
                    "from django.conf import settings; settings.DEBUG",
                    {name: value},
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(name, completed.stderr)
                for secret in ("dsn-sensitive", "port-sensitive", "invalid-sensitive-value"):
                    self.assertNotIn(secret, completed.stderr)

    def test_application_framework_and_celery_handlers_redact_after_worker_setup(self):
        script = """
import django
django.setup()
import logging
from conf.celery import app
from conf.logging import RedactingFormatter
from django.conf import settings
assert app.conf.worker_hijack_root_logger is False
app.log.setup_logging_subsystem(loglevel='INFO')
for name in ('', 'django.request', 'django.server', 'celery', 'celery.task', 'apps.media',
             'multiprocessing'):
    logger = logging.getLogger(name)
    logger.error('handler probe: %s', settings.CLERK_SECRET_KEY)
try:
    raise RuntimeError(settings.CLERK_SECRET_KEY)
except RuntimeError:
    logging.getLogger('apps.media').exception('provider rejected request')
for name in ('', 'django', 'django.server', 'celery', 'celery.task', 'multiprocessing'):
    assert all(isinstance(h.formatter, RedactingFormatter)
               for h in logging.getLogger(name).handlers)
"""
        for module in ("development", "test", "production"):
            with self.subTest(module=module):
                completed = self.run_probe(
                    f"conf.settings.{module}",
                    script,
                    {"CLERK_SECRET_KEY": "synthetic-handler-secret"},
                )
                self.assert_probe_passes(completed)
                self.assertIn("handler probe", completed.stderr)
                self.assertIn("[REDACTED]", completed.stderr)
                self.assertIn("RuntimeError", completed.stderr)
                self.assertNotIn("synthetic-handler-secret", completed.stderr)
                self.assertNotIn("test-clerk-secret", completed.stderr)

    def test_production_rejects_placeholder_secrets_and_incomplete_hsts_preload(self):
        for overrides, field in (
            (
                {"GIFFY_SHARED_SECRET": "replace-with-a-long-random-shared-secret"},
                "GIFFY_SHARED_SECRET",
            ),
            ({"DJANGO_SECRET_KEY_FALLBACKS": "short"}, "DJANGO_SECRET_KEY_FALLBACKS"),
            ({"SECURE_HSTS_PRELOAD": "true"}, "SECURE_HSTS_PRELOAD"),
        ):
            with self.subTest(field=field):
                completed = self.run_probe(
                    "conf.settings.production",
                    "from django.conf import settings; settings.DEBUG",
                    overrides,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(field, completed.stderr)

    def test_secret_key_rotation_preserves_old_signatures_with_explicit_fallback(self):
        old = "synthetic-old-key-for-rotation-test-only-with-more-than-fifty-characters"
        completed = self.run_probe(
            "conf.settings.production",
            "from django.conf import settings as s; from django.core.signing import Signer; "
            "assert len(s.SECRET_KEY_FALLBACKS) == 1; "
            "previous = Signer(key=s.SECRET_KEY_FALLBACKS[0]).sign('session-reference'); "
            "assert Signer().unsign(previous) == 'session-reference'",
            {"DJANGO_SECRET_KEY_FALLBACKS": old},
        )
        self.assert_probe_passes(completed)
