"""Clerk browser compatibility using the canonical local identity boundary."""

from django.utils.functional import SimpleLazyObject

from .identity import resolve_clerk_auth


class ClerkMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.clerk_auth = SimpleLazyObject(lambda: resolve_clerk_auth(request))
        request.clerk_user = SimpleLazyObject(lambda: request.clerk_auth.user)
        authorization = request.headers.get("Authorization", "").split()
        bearer = authorization and authorization[0].lower() == "bearer"
        cookie = not authorization and any(k.startswith("__session") for k in request.COOKIES)
        if bearer or cookie:
            request.user = SimpleLazyObject(lambda: request.clerk_auth.user)
        return self.get_response(request)
