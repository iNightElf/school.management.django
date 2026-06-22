from django.db import models
from ai_query.registry import ai_function
from teachers.models import Teacher, ClassTeacher, TeacherSubject
from accounts.permissions import is_admin_or_superuser


@ai_function(
    name="teacher_search",
    description="Search for teachers by name, email, or designation.",
    permissions=["teachers:read"],
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search term — teacher name, email, or designation",
            },
        },
        "required": ["query"],
    },
    result_columns=["Name", "Designation", "Email", "Contact"],
)
def teacher_search_handler(user, query=""):
    qs = Teacher.objects.filter(deleted_at__isnull=True)
    if query:
        qs = qs.filter(
            models.Q(name__icontains=query) |
            models.Q(email__icontains=query) |
            models.Q(designation__icontains=query)
        )
    data = list(qs.values('name', 'designation', 'email', 'contact')[:50])
    return {
        "type": "table",
        "explanation": f"Found {len(data)} teacher(s)",
        "data": data,
        "columns": ["Name", "Designation", "Email", "Contact"],
    }


@ai_function(
    name="teacher_subjects",
    description="Show subjects taught by a specific teacher.",
    permissions=["teachers:read"],
    parameters={
        "type": "object",
        "properties": {
            "teacher_name": {
                "type": "string",
                "description": "Teacher name to look up",
            },
        },
        "required": ["teacher_name"],
    },
    result_columns=["Subject", "Class"],
)
def teacher_subjects_handler(user, teacher_name=""):
    teacher = Teacher.objects.filter(deleted_at__isnull=True, name__icontains=teacher_name).first()
    if not teacher:
        return {
            "type": "summary",
            "explanation": f"No teacher found with name '{teacher_name}'",
            "data": [], "columns": [],
        }
    subs = TeacherSubject.objects.filter(teacher=teacher).select_related('subject', 'school_class')
    data = [
        {"Subject": ts.subject.name, "Class": ts.school_class.name}
        for ts in subs
    ]
    return {
        "type": "table",
        "explanation": f"Subjects taught by {teacher.name}",
        "data": data,
        "columns": ["Subject", "Class"],
    }


@ai_function(
    name="class_teachers",
    description="Show teachers assigned to a specific class (class teachers and subject teachers).",
    permissions=["teachers:read"],
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
    result_columns=["Teacher", "Role", "Subject"],
)
def class_teachers_handler(user, class_name=""):
    from core.models import SchoolClass
    cls = SchoolClass.objects.filter(name__iexact=class_name).first()
    if not cls:
        return {
            "type": "summary",
            "explanation": f"No class found with name '{class_name}'",
            "data": [], "columns": [],
        }
    data = []
    for ct in ClassTeacher.objects.filter(school_class=cls).select_related('teacher'):
        data.append({"Teacher": ct.teacher.name, "Role": "Class Teacher", "Subject": "All"})
    for ts in TeacherSubject.objects.filter(school_class=cls).select_related('teacher', 'subject'):
        data.append({"Teacher": ts.teacher.name, "Role": "Subject Teacher", "Subject": ts.subject.name})
    return {
        "type": "table",
        "explanation": f"Teachers for {cls.name}",
        "data": data,
        "columns": ["Teacher", "Role", "Subject"],
    }
