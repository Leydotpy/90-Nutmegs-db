"""Local roles: active staff administer content; superusers administer commerce."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class ActiveStaff(BasePermission):
    message = "Active staff access is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_staff)


class StaffReadOnlyOrSuperuser(ActiveStaff):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.method in SAFE_METHODS or request.user.is_superuser
        )


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or (
            request.user.is_authenticated and request.user.is_active and obj.user == request.user
        )
