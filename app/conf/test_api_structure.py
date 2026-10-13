"""Compatibility against the resolver/model registry captured before SF-04."""

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

from django.apps import apps
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.test import SimpleTestCase
from django.urls import URLPattern, get_resolver


def describe_routes(patterns, prefix="", namespaces=()):
    result = []
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if route.startswith("admin/"):
            continue
        if isinstance(pattern, URLPattern):
            callback = pattern.callback
            cls = getattr(callback, "cls", getattr(callback, "view_class", None))
            handler = cls or callback
            methods = getattr(callback, "actions", None)
            if methods is not None:
                # DRF adds HEAD to the shared action map after the first GET.
                methods = dict(methods)
                if methods.get("head") == methods.get("get"):
                    methods.pop("head", None)
            if methods is None and cls:
                methods = {m: m for m in cls.http_method_names if hasattr(cls, m)}
            result.append(
                {
                    "route": route,
                    "name": ":".join((*namespaces, pattern.name)) if pattern.name else None,
                    "callback": handler.__module__ + "." + handler.__qualname__,
                    "methods": methods,
                    "permissions": [
                        c.__module__ + "." + c.__qualname__
                        for c in getattr(cls, "permission_classes", ())
                    ],
                }
            )
        else:
            result.extend(
                describe_routes(
                    pattern.url_patterns,
                    route,
                    namespaces + ((pattern.namespace,) if pattern.namespace else ()),
                )
            )
    return result


class ApiStructureCompatibilityTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.baseline = json.loads(
            (Path(__file__).parent / "fixtures/api_structure_sf04.json").read_text()
        )

    def test_all_public_routes_actions_and_permissions_are_preserved(self):
        expected = copy.deepcopy(self.baseline["routes"])
        # SF-05 intentionally restricts dashboard access. Keep the SF-04 capture
        # unchanged and enumerate the security delta while retaining route contracts.
        for route in expected:
            if not route["route"].startswith("api/rest/dashboard/apps/"):
                continue
            callback = route["callback"]
            if callback.endswith("GiffyCallbackAPIView"):
                continue
            permission = "ActiveStaff"
            if callback == "rest_framework.routers.APIRootView":
                route["callback"] = "api.rest.dashboard.routers.StaffRootView"
            elif ".memberships.views." in callback:
                permission = "StaffReadOnlyOrSuperuser"
            route["permissions"] = ["api.rest.dashboard.permissions." + permission]
        self.assertEqual(describe_routes(get_resolver().url_patterns), expected)

    def test_model_tables_admin_and_domain_labels_are_preserved(self):
        self.assertEqual(
            sorted([m._meta.label, m._meta.db_table] for m in apps.get_models()),
            self.baseline["models"],
        )
        self.assertEqual(
            sorted(m._meta.label for m in admin.site._registry), self.baseline["admin"]
        )
        self.assertEqual(
            [[c.name, c.label] for c in apps.get_app_configs()],
            [c for c in self.baseline["apps"] if not c[0].startswith("api")],
        )

    def test_entitlement_representations_remain_api_owned(self):
        from api.rest.dashboard.apps.memberships.serializers import _get_serializer_for_content_type
        from api.rest.dashboard.apps.podcasts.serializers import (
            EpisodeModelSerializer,
            PodcastModelSerializer,
        )

        for model, serializer in (
            ("episode", EpisodeModelSerializer),
            ("podcast", PodcastModelSerializer),
        ):
            with self.subTest(model=model):
                self.assertIs(
                    _get_serializer_for_content_type(
                        ContentType(app_label="podcasts", model=model)
                    ),
                    serializer,
                )

    def test_fresh_startup_does_not_load_api_or_removed_framework(self):
        probe = """
import importlib.abc
import sys
class RejectLegacy(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {'core.application', 'core.loading', 'core.exceptions',
                        'api.rest.core', 'api.rest.utils.loading'}:
            raise AssertionError('Legacy import: ' + fullname)
sys.meta_path.insert(0, RejectLegacy())
import django
django.setup()
assert not any(n == 'api' or n.startswith('api.') for n in sys.modules)
from django.urls import get_resolver
list(get_resolver().url_patterns)
from django.core.management import call_command
call_command('check')
"""
        result = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, "DJANGO_SETTINGS_MODULE": "conf.settings.test"},
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
