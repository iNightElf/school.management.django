from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache


_INVALIDATE_KEYS = ['dashboard_summary']


def _invalidate_dashboard():
    for key in _INVALIDATE_KEYS:
        cache.delete(key)


@receiver([post_save, post_delete], sender='students.Student')
def invalidate_on_student_change(sender, **kwargs):
    _invalidate_dashboard()


@receiver([post_save, post_delete], sender='teachers.Teacher')
def invalidate_on_teacher_change(sender, **kwargs):
    _invalidate_dashboard()


@receiver([post_save, post_delete], sender='staff.Staff')
def invalidate_on_staff_change(sender, **kwargs):
    _invalidate_dashboard()
