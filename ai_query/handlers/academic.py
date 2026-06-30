from datetime import date, timedelta
from django.db import models
from ai_query.registry import ai_function
from accounts.permissions import is_admin_or_superuser


@ai_function(
    name="homework_by_class",
    description="Get published homework for a specific class. Returns topic, subject, due date.",
    permissions=["academic:read"],
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
    result_columns=["Date", "Subject", "Topic", "Due Date", "Teacher"],
)
def homework_by_class_handler(user, class_name=""):
    from core.models import SchoolClass
    from academic.models import Homework
    cls = SchoolClass.objects.filter(name__iexact=class_name).first()
    if not cls:
        return {"type": "summary", "explanation": f"No class found with name '{class_name}'", "data": [], "columns": []}
    qs = Homework.objects.filter(school_class=cls, published=True).select_related('subject', 'teacher').order_by('-date')[:50]
    data = [{"Date": str(h.date), "Subject": h.subject.name, "Topic": h.topic, "Due Date": str(h.due_date), "Teacher": h.teacher.name if h.teacher else ""} for h in qs]
    return {"type": "table", "explanation": f"Published homework for {class_name} ({len(data)} items)", "data": data, "columns": ["Date", "Subject", "Topic", "Due Date", "Teacher"]}


@ai_function(
    name="diary_by_class",
    description="Get diary entries (what was taught) for a specific class.",
    permissions=["academic:read"],
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
    result_columns=["Date", "Subject", "Topic", "Teacher"],
)
def diary_by_class_handler(user, class_name=""):
    from core.models import SchoolClass
    from academic.models import Diary
    cls = SchoolClass.objects.filter(name__iexact=class_name).first()
    if not cls:
        return {"type": "summary", "explanation": f"No class found with name '{class_name}'", "data": [], "columns": []}
    qs = Diary.objects.filter(school_class=cls).select_related('subject', 'teacher').order_by('-date')[:50]
    data = [{"Date": str(d.date), "Subject": d.subject.name, "Topic": d.topic, "Teacher": d.teacher.name if d.teacher else ""} for d in qs]
    return {"type": "table", "explanation": f"Diary entries for {class_name} ({len(data)} items)", "data": data, "columns": ["Date", "Subject", "Topic", "Teacher"]}


@ai_function(
    name="weekly_routine",
    description="Get the weekly class routine/schedule for a specific class, showing subjects per period each day.",
    permissions=["academic:read"],
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
    result_columns=["Day", "Period", "Subject", "Teacher"],
)
def weekly_routine_handler(user, class_name=""):
    from core.models import SchoolClass
    from academic.models import RoutineTemplate
    cls = SchoolClass.objects.filter(name__iexact=class_name).first()
    if not cls:
        return {"type": "summary", "explanation": f"No class found with name '{class_name}'", "data": [], "columns": []}
    qs = RoutineTemplate.objects.filter(school_class=cls).select_related('subject', 'teacher').order_by('day', 'period_number')[:100]
    data = [{"Day": r.get_day_display(), "Period": str(r.period_number), "Subject": r.subject.name, "Teacher": r.teacher.name if r.teacher else ""} for r in qs]
    return {"type": "table", "explanation": f"Weekly routine for {class_name}", "data": data, "columns": ["Day", "Period", "Subject", "Teacher"]}


@ai_function(
    name="exam_routine",
    description="Get exam schedule/routine for a specific class.",
    permissions=["academic:read"],
    parameters={
        "type": "object",
        "properties": {
            "class_name": {
                "type": "string",
                "description": "Class name (e.g. 'Class 7', 'Seven')",
            },
            "exam_name": {
                "type": "string",
                "description": "Exam name filter (e.g. 'Mid Term', 'Final')",
            },
        },
        "required": ["class_name"],
    },
    result_columns=["Exam", "Subject", "Date", "Start", "End", "Room"],
)
def exam_routine_handler(user, class_name="", exam_name=""):
    from core.models import SchoolClass
    from academic.models import ExamRoutine
    cls = SchoolClass.objects.filter(name__iexact=class_name).first()
    if not cls:
        return {"type": "summary", "explanation": f"No class found with name '{class_name}'", "data": [], "columns": []}
    qs = ExamRoutine.objects.filter(school_class=cls).select_related('subject').order_by('date', 'start_time')
    if exam_name:
        qs = qs.filter(exam_name__iexact=exam_name)
    data = [{"Exam": r.exam_name, "Subject": r.subject.name, "Date": str(r.date), "Start": str(r.start_time)[:5], "End": str(r.end_time)[:5] if r.end_time else "", "Room": r.room} for r in qs[:100]]
    return {"type": "table", "explanation": f"Exam schedule for {class_name}" + (f" — {exam_name}" if exam_name else ""), "data": data, "columns": ["Exam", "Subject", "Date", "Start", "End", "Room"]}


@ai_function(
    name="lesson_plans",
    description="Get lesson plans/topics for a class and subject, showing what topics are being taught each week.",
    permissions=["academic:read"],
    parameters={
        "type": "object",
        "properties": {
            "class_name": {
                "type": "string",
                "description": "Class name (e.g. 'Class 7', 'Seven')",
            },
            "subject_name": {
                "type": "string",
                "description": "Subject name filter",
            },
        },
        "required": ["class_name"],
    },
    result_columns=["Subject", "Week Start", "Topic", "Completed"],
)
def lesson_plans_handler(user, class_name="", subject_name=""):
    from core.models import SchoolClass
    from academic.models import LessonPlan, RoutineTemplate
    cls = SchoolClass.objects.filter(name__iexact=class_name).first()
    if not cls:
        return {"type": "summary", "explanation": f"No class found with name '{class_name}'", "data": [], "columns": []}
    qs = LessonPlan.objects.filter(routine_template__school_class=cls).select_related('routine_template__subject').order_by('-week_start', 'routine_template__period_number')
    if subject_name:
        qs = qs.filter(routine_template__subject__name__iexact=subject_name)
    data = [{"Subject": lp.routine_template.subject.name, "Week Start": str(lp.week_start), "Topic": lp.topic, "Completed": "Yes" if lp.completed else "No"} for lp in qs[:50]]
    return {"type": "table", "explanation": f"Lesson plans for {class_name}" + (f" — {subject_name}" if subject_name else ""), "data": data, "columns": ["Subject", "Week Start", "Topic", "Completed"]}
