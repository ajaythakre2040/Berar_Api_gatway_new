from rest_framework.permissions import BasePermission

class IsClientAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request, "client") and request.client is not None
