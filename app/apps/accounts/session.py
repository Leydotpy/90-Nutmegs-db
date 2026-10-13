"""Carry server-owned anonymous session identity across Django login rotation."""

from django.contrib.auth import SESSION_KEY


class AnonymousSessionIdentityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Never take a queue/session identity from request data or a custom cookie.
        request._anonymous_session_key = None
        # Django login is a POST. Leave read-only requests and health probes
        # lazy, even when a browser sends an existing session cookie.
        if (
            request.method == "POST"
            and request.session.session_key
            and not request.session.get(SESSION_KEY)
        ):
            request._anonymous_session_key = request.session.session_key
        return self.get_response(request)
