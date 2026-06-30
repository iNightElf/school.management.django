from django.contrib import admin
from .models import RoutineTemplate, LessonPlan, Homework, Diary, ExamRoutine


@admin.register(RoutineTemplate)
class RoutineTemplateAdmin(admin.ModelAdmin):
    list_display = ['school_class', 'day', 'period_number', 'subject', 'teacher']
    list_filter = ['school_class', 'day', 'teacher']
    search_fields = ['school_class__name', 'subject__name', 'teacher__name']


@admin.register(LessonPlan)
class LessonPlanAdmin(admin.ModelAdmin):
    list_display = ['routine_template', 'week_start', 'topic', 'completed']
    list_filter = ['completed', 'week_start']


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ['subject', 'school_class', 'date', 'due_date', 'published']
    list_filter = ['published', 'school_class', 'subject']


@admin.register(Diary)
class DiaryAdmin(admin.ModelAdmin):
    list_display = ['subject', 'school_class', 'date', 'topic']
    list_filter = ['school_class', 'subject', 'date']


@admin.register(ExamRoutine)
class ExamRoutineAdmin(admin.ModelAdmin):
    list_display = ['exam_name', 'school_class', 'subject', 'date', 'start_time']
    list_filter = ['exam_name', 'school_class', 'date']
