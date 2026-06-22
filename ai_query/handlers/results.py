from django.db import models
from ai_query.registry import ai_function
from results.models import Result
from accounts.permissions import is_admin_or_superuser


@ai_function(
    name="result_summary",
    description="Get exam result summary for a class within a term and session.",
    permissions=["results:read"],
    parameters={
        "type": "object",
        "properties": {
            "class_name": {
                "type": "string",
                "description": "Class name (e.g. 'Class 7', 'Seven')",
            },
            "term": {
                "type": "string",
                "description": "Term name (e.g. 'Mid Term', 'Final')",
            },
            "session": {
                "type": "string",
                "description": "Academic session (e.g. '2025')",
            },
        },
        "required": ["class_name", "term"],
    },
    result_columns=["Student", "Marks"],
)
def result_summary_handler(user, class_name="", term="", session=""):
    from students.models import Student
    from core.models import SchoolClass
    cls = SchoolClass.objects.filter(name__iexact=class_name).first()
    if not cls:
        return {
            "type": "summary",
            "explanation": f"No class found with name '{class_name}'",
            "data": [], "columns": [],
        }
    qs = Result.objects.filter(student__school_class=cls, term__iexact=term)
    if session:
        qs = qs.filter(session=session)
    if not is_admin_or_superuser(user):
        from teachers.models import ClassTeacher
        if not ClassTeacher.objects.filter(teacher__user=user, school_class=cls).exists():
            return {
                "type": "summary",
                "explanation": f"You don't have access to results for {class_name}",
                "data": [], "columns": [],
            }
    data = []
    for r in qs.select_related('student').only('student__name', 'marks')[:100]:
        data.append({
            "Student": r.student.name,
            "Marks": str(dict(r.marks)) if r.marks else "N/A",
        })
    return {
        "type": "table",
        "explanation": f"Results for {class_name} — {term} ({len(data)} students)",
        "data": data,
        "columns": ["Student", "Marks"],
    }


@ai_function(
    name="result_detail",
    description="Get detailed exam result for a specific student by student ID or name.",
    permissions=["results:read"],
    parameters={
        "type": "object",
        "properties": {
            "student_id": {
                "type": "string",
                "description": "Student ID or name",
            },
            "term": {
                "type": "string",
                "description": "Term name (e.g. 'Mid Term', 'Final')",
            },
            "session": {
                "type": "string",
                "description": "Academic session (e.g. '2025')",
            },
        },
        "required": ["student_id", "term"],
    },
    result_columns=["Subject", "Marks"],
)
def result_detail_handler(user, student_id="", term="", session=""):
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
                "explanation": f"You don't have access to results for this student",
                "data": [], "columns": [],
            }
    qs = Result.objects.filter(student=student, term__iexact=term)
    if session:
        qs = qs.filter(session=session)
    result = qs.first()
    if not result:
        return {
            "type": "summary",
            "explanation": f"No result found for {student.name} in {term}",
            "data": [], "columns": [],
        }
    marks = result.marks or {}
    data = [{"Subject": k, "Marks": str(v)} for k, v in marks.items()]
    return {
        "type": "table",
        "explanation": f"Result for {student.name} ({student.student_id}) — {term}",
        "data": data,
        "columns": ["Subject", "Marks"],
    }
