from django.contrib import admin
from .models import Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'email', 'contact', 'created_at')
    list_filter = ('role',)
    search_fields = ('name', 'email', 'contact')
    readonly_fields = ('id', 'created_at')
