from rest_framework.permissions import BasePermission, SAFE_METHODS
from guardian.core import ObjectPermissionChecker

msg = f"Access denied. you do not have sufficient permission to continue"


class CachedObjectOwnerPerm(BasePermission):
    message = msg

    def has_object_permission(self, request, view, obj):
        checker = ObjectPermissionChecker(request.user)
        return checker.has_perm("profile_user", obj)


class ObjectOwnerPerm(BasePermission):
    message = msg

    def has_object_permission(self, request, view, obj):
        return request.user.has_perm("profiles.profile_user", obj)


class IsCEO(BasePermission):
    message = msg
    SAFE_METHODS = ['GET']

    def has_permission(self, request, view):
        user = request.user
        return bool(request.method in self.SAFE_METHODS or
                    user.has_perm("profiles.c_e_o"))


class IsManager(BasePermission):
    message = msg

    def has_permission(self, request, view):
        user = request.user
        return bool(user.has_perm("profiles.manager"))


class IsDirector(BasePermission):
    message = msg

    def has_permission(self, request, view):
        return bool(request.user.has_perm("profiles.director"))


class IsSecretary(BasePermission):
    message = msg

    def has_permission(self, request, view):
        return bool(request.user.has_perm("profiles.secretary"))


class IsPromoter(BasePermission):
    message = msg

    def has_permission(self, request, view):
        return request.user.has_perm("profiles.promoter")


class IsOwnerOrReadOnly(BasePermission):
    message = msg

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user


class IsOwnerOrError(BasePermission):
    message = msg

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsAdmin(BasePermission):
    message = msg

    def has_permission(self, request, view):
        return request.user.has_perm("profiles.promoter") or request.user.has_perm(
            "profiles.secretary") or request.user.has_perm("profiles.director") or request.user.has_perm(
            "profiles.c_e_o")
