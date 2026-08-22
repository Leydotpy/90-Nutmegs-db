from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import generics, status, response
from django.contrib.auth import get_user_model
from ..core import get_model

User = get_user_model()
BAD_REQ = status.HTTP_400_BAD_REQUEST
REQ_OK = status.HTTP_200_OK
REQ_NOT_FOUND = status.HTTP_404_NOT_FOUND


class RoleAssignor:
    def get_permission(self, role, user_id):
        _model = self.get_object(user_id)
        return Permission.objects.get(codename=role, content_type=_model,)

    def get_object(self, user_id):
        user = self.get_user(user_id)
        return ContentType.objects.get_for_model(user)

    def get_user(self, user_id):
        return generics.get_object_or_404(User.objects.all(), id=user_id)

    def assign_role(self, perm, user, role):
        if self.user_has_no_existing_perm(user):
            user.user_permissions.add(perm)
            return True
        return False

    def remove_role(self, perm, user, role):
        if not self.user_has_no_existing_perm(user):
            user.user_permissions.remove(perm)
            return True
        return False

    def user_has_no_existing_perm(self, user):
        """
        :param user: The request user which we are checking if has an existing permission
        :return: Boolean, True if the request user has the specified permissions or False
        """
        if user.has_perm("profiles.c_e_o"):
            return False
        elif user.has_perm("profiles.director"):
            return False
        elif user.has_perm("profiles.user_support"):
            return False
        elif user.has_perm("profiles.forum_admin"):
            return False
        elif user.has_perm("profiles.promoter"):
            return False
        return True
