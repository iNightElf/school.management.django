from rest_framework.permissions import BasePermission
from accounts.permissions import has_permission


class CanMarkAttendance(BasePermission):
    def has_permission(self, request, view):
        return has_permission(request.user, 'students:write')
