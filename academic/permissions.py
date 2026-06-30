from accounts.permissions import has_permission, is_admin_or_superuser, is_class_teacher_of, can_teach_subject
from rest_framework.permissions import BasePermission


def get_teacher_profile(user):
    return getattr(user, 'teacher_profile', None)
