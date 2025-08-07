from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """
    Allows access only to users with admin user_type.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'admin' # Checks that the user is logged in Only users with user_type 'admin' pass.

