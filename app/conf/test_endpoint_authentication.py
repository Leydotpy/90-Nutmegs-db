"""Every DRF route has the same explicit credential policy or signed callback exemption."""

from api.rest.authentication import ClerkBearerAuthentication
from api.rest.dashboard.apps.promotions.views import GiffyCallbackAPIView
from django.test import SimpleTestCase
from django.urls import URLPattern, get_resolver
from rest_framework.authentication import SessionAuthentication


def api_callbacks(patterns, prefix=""):
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if isinstance(pattern, URLPattern):
            if route.startswith("api/"):
                yield route, pattern.callback
        else:
            yield from api_callbacks(pattern.url_patterns, route)


class EndpointAuthenticationTests(SimpleTestCase):
    def test_all_api_routes_use_bearer_then_csrf_session_or_signed_provider_callback(self):
        count = 0
        for route, callback in api_callbacks(get_resolver().url_patterns):
            with self.subTest(route=route):
                cls = callback.cls
                view = cls(**callback.initkwargs)
                expected = (
                    ()
                    if cls is GiffyCallbackAPIView
                    else (ClerkBearerAuthentication, SessionAuthentication)
                )
                self.assertEqual(tuple(view.authentication_classes), expected)
                count += 1
        self.assertEqual(count, 172)
