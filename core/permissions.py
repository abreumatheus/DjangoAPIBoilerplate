from rest_framework.permissions import IsAdminUser, SAFE_METHODS, IsAuthenticated, BasePermission


class IsAdminUserOrReadOnly(IsAdminUser):
    def has_permission(self, request, view):
        is_admin = super().has_permission(request, view)
        is_authenticated = IsAuthenticated()
        is_authenticated = is_authenticated.has_permission(request, view)

        return is_admin or is_authenticated and request.method in SAFE_METHODS


class UserCustomPermissionsSet(BasePermission):
    def has_permission(self, request, _):
        user = request.user

        if user.is_staff:
            return True
        if request.method == 'POST':
            return True
        if request.path == f'/api/user/{user.id}/' and user.is_authenticated:
            return True
        if request.path != '/api/user/' and request.method in SAFE_METHODS:
            return True
