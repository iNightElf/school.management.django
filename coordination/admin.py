from django.contrib import admin
from .models import (
    Alert, Intervention, ParentCommunication,
    TeacherWeeklyReport, ClassTest, ClassTestMark, CoordinatorTask,
)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'alert_type', 'status', 'severity', 'created_by', 'created_at')
    list_filter = ('alert_type', 'status', 'severity')
    search_fields = ('title', 'description', 'student__name')


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ('alert', 'action_taken', 'status', 'followup_date', 'created_by')
    list_filter = ('status',)


@admin.register(ParentCommunication)
class ParentCommunicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'communication_type', 'followup_date', 'created_by', 'created_at')
    list_filter = ('communication_type',)


@admin.register(TeacherWeeklyReport)
class TeacherWeeklyReportAdmin(admin.ModelAdmin):
    list_display = ('class_teacher', 'week_start_date', 'status', 'submitted_at')
    list_filter = ('status',)


@admin.register(ClassTest)
class ClassTestAdmin(admin.ModelAdmin):
    list_display = ('test_name', 'school_class', 'subject', 'test_date', 'total_marks', 'created_by')
    list_filter = ('school_class', 'subject')


@admin.register(ClassTestMark)
class ClassTestMarkAdmin(admin.ModelAdmin):
    list_display = ('class_test', 'student', 'marks_obtained')
    list_filter = ('class_test',)


@admin.register(CoordinatorTask)
class CoordinatorTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'due_date', 'assigned_to', 'created_by')
    list_filter = ('status', 'priority')
