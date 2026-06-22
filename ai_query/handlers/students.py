from django.db import models
from ai_query.registry import ai_function
from students.models import Student
from accounts.permissions import is_admin_or_superuser, is_class_teacher_of


@ai_function(
    name="search_student",
    description="Search for students by name, roll, or student ID. Returns matching students.",
    permissions=["students:read"],
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search term — student name, roll number, or student ID",
            },
            "class_name": {
                "type": "string",
                "description": "Class name filter (e.g. 'Class 7', 'Seven')",
            },
        },
        "required": ["query"],
    },
    result_columns=["Student ID", "Name", "Class", "Roll", "Session"],
)
def search_student_handler(user, query="", class_name=None):
    qs = Student.objects.filter(deleted_at__isnull=True)
    if not is_admin_or_superuser(user):
        from teachers.models import ClassTeacher
        ct = ClassTeacher.objects.filter(teacher__user=user).values_list('school_class_id', flat=True)
        qs = qs.filter(school_class_id__in=list(ct))
    if class_name:
        qs = qs.filter(school_class__name__iexact=class_name)
    if query:
        qs = qs.filter(
            models.Q(name__icontains=query) |
            models.Q(student_id__icontains=query) |
            models.Q(roll__icontains=query)
        )
    data = list(qs.select_related('school_class').values('student_id', 'name', 'school_class__name', 'roll', 'session')[:50])
    count = len(data)
    return {
        "type": "table",
        "explanation": f"Found {count} student(s) matching '{query}'" if query else f"Showing {count} student(s)",
        "data": data,
        "columns": ["Student ID", "Name", "Class", "Roll", "Session"],
    }


@ai_function(
    name="student_profile",
    description="Get full profile of a specific student by student ID or name.",
    permissions=["students:read"],
    parameters={
        "type": "object",
        "properties": {
            "student_id": {
                "type": "string",
                "description": "Student ID or name to look up",
            },
        },
        "required": ["student_id"],
    },
    result_columns=["Field", "Value"],
)
def student_profile_handler(user, student_id=""):
    qs = Student.objects.filter(deleted_at__isnull=True)
    if not is_admin_or_superuser(user):
        from teachers.models import ClassTeacher
        ct = ClassTeacher.objects.filter(teacher__user=user).values_list('school_class_id', flat=True)
        qs = qs.filter(school_class_id__in=list(ct))
    student = qs.filter(
        models.Q(student_id__iexact=student_id) | models.Q(name__iexact=student_id)
    ).select_related('school_class').first()
    if not student:
        return {
            "type": "summary",
            "explanation": f"No student found with ID or name '{student_id}'",
            "data": [], "columns": [],
        }
    data = [
        {"Field": "Student ID", "Value": student.student_id},
        {"Field": "Name", "Value": student.name},
        {"Field": "Class", "Value": student.school_class.name if student.school_class else "N/A"},
        {"Field": "Roll", "Value": student.roll},
        {"Field": "Session", "Value": student.session},
        {"Field": "Father", "Value": student.father_name},
        {"Field": "Mother", "Value": student.mother_name},
        {"Field": "Contact", "Value": student.contact},
    ]
    return {
        "type": "table",
        "explanation": f"Profile for {student.name} ({student.student_id})",
        "data": data, "columns": ["Field", "Value"],
    }


@ai_function(
    name="class_list",
    description="List all students in a specific class.",
    permissions=["students:read"],
    parameters={
        "type": "object",
        "properties": {
            "class_name": {
                "type": "string",
                "description": "Class name (e.g. 'Class 7', 'Seven')",
            },
        },
        "required": ["class_name"],
    },
    result_columns=["Student ID", "Name", "Roll"],
)
def class_list_handler(user, class_name=""):
    qs = Student.objects.filter(deleted_at__isnull=True, school_class__name__iexact=class_name)
    if not is_admin_or_superuser(user):
        from teachers.models import ClassTeacher
        ct = ClassTeacher.objects.filter(teacher__user=user).values_list('school_class_id', flat=True)
        qs = qs.filter(school_class_id__in=list(ct))
        if not qs.exists():
            return {
                "type": "summary",
                "explanation": f"You don't have access to view students in {class_name}",
                "data": [], "columns": [],
            }
    data = list(qs.values('student_id', 'name', 'roll').order_by('roll')[:200])
    return {
        "type": "table",
        "explanation": f"Students in {class_name} ({len(data)} shown)",
        "data": data,
        "columns": ["Student ID", "Name", "Roll"],
    }
