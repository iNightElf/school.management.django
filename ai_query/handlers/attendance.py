from django.db import models
from ai_query.registry import ai_function
from attendance.models import AttendanceRecord
from accounts.permissions import is_admin_or_superuser


@ai_function(
    name="attendance_summary",
    description="Get attendance summary (present/absent/late/excused counts) for a class within a date range.",
    permissions=["students:read"],
    parameters={
        "type": "object",
        "properties": {
            "class_name": {
                "type": "string",
                "description": "Class name (e.g. 'Class 7', 'Seven')",
            },
            "date_from": {
                "type": "string",
                "description": "Start date (YYYY-MM-DD), defaults to today",
            },
            "date_to": {
                "type": "string",
                "description": "End date (YYYY-MM-DD), defaults to today",
            },
        },
        "required": ["class_name"],
    },
    result_columns=["Date", "Present", "Absent", "Late", "Excused", "Total"],
)
def attendance_summary_handler(user, class_name="", date_from=None, date_to=None):
    from core.models import SchoolClass
    cls = SchoolClass.objects.filter(name__iexact=class_name).first()
    if not cls:
        return {
            "type": "summary",
            "explanation": f"No class found with name '{class_name}'",
            "data": [], "columns": [],
        }
    if not is_admin_or_superuser(user):
        from teachers.models import ClassTeacher
        if not ClassTeacher.objects.filter(teacher__user=user, school_class=cls).exists():
            return {
                "type": "summary",
                "explanation": f"You don't have access to attendance for {class_name}",
                "data": [], "columns": [],
            }
    from datetime import date
    d_from = date_from or date.today().isoformat()
    d_to = date_to or d_from
    recs = (
        AttendanceRecord.objects
        .filter(school_class=cls, date__gte=d_from, date__lte=d_to)
        .values('date')
        .annotate(
            present=models.Count('id', filter=models.Q(status='present')),
            absent=models.Count('id', filter=models.Q(status='absent')),
            late=models.Count('id', filter=models.Q(status='late')),
            excused=models.Count('id', filter=models.Q(status='excused')),
            total=models.Count('id'),
        )
        .order_by('date')
    )
    data = list(recs)
    return {
        "type": "table",
        "explanation": f"Attendance summary for {class_name} ({d_from} to {d_to})",
        "data": data,
        "columns": ["Date", "Present", "Absent", "Late", "Excused", "Total"],
    }


@ai_function(
    name="attendance_detail",
    description="Get detailed attendance for a specific student by student ID or name.",
    permissions=["students:read"],
    parameters={
        "type": "object",
        "properties": {
            "student_id": {
                "type": "string",
                "description": "Student ID or name",
            },
            "date_from": {
                "type": "string",
                "description": "Start date (YYYY-MM-DD)",
            },
            "date_to": {
                "type": "string",
                "description": "End date (YYYY-MM-DD)",
            },
        },
        "required": ["student_id"],
    },
    result_columns=["Date", "Status", "Term"],
)
def attendance_detail_handler(user, student_id="", date_from=None, date_to=None):
    from students.models import Student
    student = Student.objects.filter(deleted_at__isnull=True).filter(
        models.Q(student_id__iexact=student_id) | models.Q(name__icontains=student_id)
    ).first()
    if not student:
        return {
            "type": "summary",
            "explanation": f"No student found with ID or name '{student_id}'",
            "data": [], "columns": [],
        }
    if not is_admin_or_superuser(user):
        from teachers.models import ClassTeacher
        if not ClassTeacher.objects.filter(teacher__user=user, school_class=student.school_class).exists():
            return {
                "type": "summary",
                "explanation": f"You don't have access to attendance records for this student",
                "data": [], "columns": [],
            }
    qs = AttendanceRecord.objects.filter(student=student)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    data = list(qs.values('date', 'status', 'term').order_by('-date')[:200])
    return {
        "type": "table",
        "explanation": f"Attendance for {student.name} ({student.student_id})",
        "data": data,
        "columns": ["Date", "Status", "Term"],
    }
