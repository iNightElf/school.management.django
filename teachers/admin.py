from django.contrib import admin
from .models import Teacher, ClassTeacher, TeacherSubject


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'designation', 'email', 'user', 'contact', 'created_at')
    list_filter = ('designation',)
    search_fields = ('name', 'email', 'contact')
    readonly_fields = ('id', 'created_at')


@admin.register(ClassTeacher)
class ClassTeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'school_class', 'created_at')
    list_filter = ('school_class',)
    search_fields = ('teacher__name',)
    readonly_fields = ('id', 'created_at')


@admin.register(TeacherSubject)
class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'school_class', 'created_at')
    list_filter = ('school_class', 'subject')
    search_fields = ('teacher__name',)
    readonly_fields = ('id', 'created_at')
