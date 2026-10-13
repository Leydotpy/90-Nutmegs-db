"""Web entrypoints must stay usable without worker libraries or startup I/O."""

from __future__ import annotations

import subprocess
import sys
import unittest

from conf import tests as fixtures

WEB_PROBE = """
import importlib
import importlib.abc
import sys
from unittest.mock import patch

blocked = {'torch', 'whisper', 'faiss', 'numpy', 'pandas', 'scipy', 'sklearn',
           'tensorflow', 'joblib', 'openai'}
attempts = []
class RejectWorkerLibraries(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in blocked or fullname.startswith('google.cloud'):
            attempts.append(fullname)
            raise AssertionError('Worker library imported by web: ' + fullname)
sys.meta_path.insert(0, RejectWorkerLibraries())

with patch('socket.socket.connect', side_effect=AssertionError('Startup network I/O')), \
     patch('subprocess.Popen', side_effect=AssertionError('Startup subprocess')), \
     patch('django.db.backends.utils.CursorWrapper.execute',
           side_effect=AssertionError('Startup database query')):
    for module in ('conf.wsgi', 'conf.asgi', 'conf.urls',
                   'apps.recommendation.management.commands.train_recommenders',
                   'apps.recommendation.management.commands.generate_dataset'):
        importlib.import_module(module)
    from django.conf import settings
    from django.test import Client
    result = Client().get('/health/live/', secure=True,
                          HTTP_HOST=settings.ALLOWED_HOSTS[0])
    assert result.status_code == 200, result.status_code
    assert result.json()['status'] == 'ok'
assert not attempts, attempts
assert not blocked.intersection(sys.modules)
print('web startup and liveness isolated')
"""


class WebRuntimeIsolationTests(unittest.TestCase):
    def test_web_entrypoints_never_import_worker_libraries_or_start_external_work(self):
        for module in ("development", "test", "production"):
            with self.subTest(module=module):
                values = fixtures.REQUIRED_PRODUCTION_ENV.copy() if module == "production" else {}
                values.update(
                    DJANGO_ALLOWED_HOSTS="example.test",
                    DJANGO_SECRET_KEY_FALLBACKS="",
                    CORS_ALLOWED_ORIGINS="",
                    CSRF_TRUSTED_ORIGINS="",
                    TRUST_PROXY_SSL_HEADER="false",
                    SECURE_HSTS_SECONDS="0",
                    SECURE_HSTS_INCLUDE_SUBDOMAINS="false",
                    SECURE_HSTS_PRELOAD="false",
                )
                result = subprocess.run(
                    [sys.executable, "-c", WEB_PROBE],
                    cwd=fixtures.APP_DIR,
                    env=fixtures.SettingsImportTests()._environment(
                        f"conf.settings.{module}", values
                    ),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("web startup and liveness isolated", result.stdout)
