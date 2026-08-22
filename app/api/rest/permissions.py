# apps/region/api/permissions.py
from rest_framework import permissions

def ModelPermissionRequired(action: str):
    """
    Returns a DRF permission class which enforces that the requesting user
    has the model-level permission for `action` (e.g. 'delete', 'change', 'add').
    The permission is checked against the object class when used via
    has_object_permission.

    Usage:
      @action(..., permission_classes=[ModelPermissionRequired('delete')])
    or programmatically:
      perm = ModelPermissionRequired('delete')()
      perm.has_object_permission(request, view, obj)
    """

    class _ModelPermission(permissions.BasePermission):
        """
        Permission that:
         - Allows safe methods;
         - For unsafe methods requires the user to be authenticated in has_permission;
         - For object-level checks, inspects the object's model meta and checks
           user.has_perm(f"{app_label}.{action}_{model_name}")
        """

        def has_permission(self, request, view):
            # Safe methods allowed
            if request.method in permissions.SAFE_METHODS:
                return True
            # writes require authentication (object-level fine-grained check will follow)
            return bool(request.user and request.user.is_authenticated)

        def has_object_permission(self, request, view, obj):
            # If safe method, allow
            if request.method in permissions.SAFE_METHODS:
                return True

            if obj is None:
                return False

            model = obj.__class__
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            perm_codename = f"{action}_{model_name}" if action not in ("delete", "add", "change") else f"{action}_{model_name}"
            # for typical Django perms this yields e.g. 'region.delete_country', 'leagues.change_league'
            perm = f"{app_label}.{perm_codename}"

            return request.user.has_perm(perm)

    _ModelPermission.__name__ = f"ModelPermission_{action}"
    return _ModelPermission
