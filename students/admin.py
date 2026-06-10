from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_id', 'school_class', 'roll', 'session', 'created_at')
    list_filter = ('session', 'school_class')
    search_fields = ('name', 'student_id', 'father_name', 'contact')
    readonly_fields = ('id', 'student_id', 'created_at')
