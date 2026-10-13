from rest_framework.routers import APIRootView, DefaultRouter

from .permissions import ActiveStaff


class StaffRootView(APIRootView):
    permission_classes = (ActiveStaff,)


class StaffRouter(DefaultRouter):
    APIRootView = StaffRootView
