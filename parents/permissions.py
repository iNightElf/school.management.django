from rest_framework.permissions import BasePermission


class IsParentOfStudent(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role == 'parent':
            return True
        return False

    def has_object_permission(self, request, view, obj):
        parent_links = request.user.parent_links.values_list('student_id', flat=True)
        return obj.student_id in parent_links
