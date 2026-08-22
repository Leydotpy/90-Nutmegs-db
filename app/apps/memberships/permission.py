from rest_framework.permissions import BasePermission
from .access import AccessService

class HasSubscriptionOrEntitlement(BasePermission):
    """
    Allow if AccessService says the user has access to the object.
    Views using this permission must implement `get_object()` or pass the object to check.
    """

    def has_permission(self, request, view):
        # Allow the view-level permission; actual object permission evaluated below.
        # Some list endpoints may want to allow listing of public items; keep True.
        return True

    def has_object_permission(self, request, view, obj):
        service = AccessService.get_instance()
        return service.has_access(request.user, obj)
