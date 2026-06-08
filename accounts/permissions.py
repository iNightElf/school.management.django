from rest_framework.permissions import BasePermission

ROLE_PERMISSIONS = {
    'admin': [
        'students:read', 'students:write',
        'teachers:read', 'teachers:write',
        'staff:read', 'staff:write',
        'books:read', 'books:write',
        'classes:read', 'classes:write',
        'subjects:read', 'subjects:write', 'subjects:admin',
        'results:read', 'results:write', 'results:admin',
        'finance:read', 'finance:write', 'finance:admin',
        'users:read', 'users:write',
        'audit:read',
        'academic-years:read', 'academic-years:write',
    ],
    'teacher': [
        'students:read', 'students:write',
        'teachers:read',
        'staff:read',
        'books:read',
        'classes:read',
        'subjects:read',
        'results:read', 'results:write',
        'academic-years:read',
    ],
    'accountant': [
        'students:read',
        'teachers:read',
        'staff:read',
        'books:read',
        'classes:read',
        'finance:read', 'finance:write',
        'academic-years:read',
    ],
    'super_viewer': [
        'students:read',
        'teachers:read',
        'staff:read',
        'books:read',
        'classes:read',
        'subjects:read',
        'results:read',
        'finance:read',
        'academic-years:read',
    ],
    'viewer': [],
}


def has_permission(user, permission):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    perms = ROLE_PERMISSIONS.get(user.role, [])
    return permission in perms


class HasPermission(BasePermission):
    def __init__(self, permission):
        self.permission = permission
        super().__init__()

    def has_permission(self, request, view):
        return has_permission(request.user, self.permission)


def require_permission(permission):
    class CheckPermission(BasePermission):
        def has_permission(self, request, view):
            return has_permission(request.user, permission)
    return CheckPermission
