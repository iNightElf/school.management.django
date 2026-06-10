from django.contrib import admin
from .models import Result


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'session', 'term', 'created_at')
    list_filter = ('session', 'term')
    search_fields = ('student_id',)
    readonly_fields = ('id', 'created_at')
