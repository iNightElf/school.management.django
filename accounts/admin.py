from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerification


class ParentStudentLinkInline(admin.TabularInline):
    from parents.models import ParentStudentLink
    model = ParentStudentLink
    extra = 1
    autocomplete_fields = ['student']
    fk_name = 'parent'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [ParentStudentLinkInline]
    model = User
    list_display = ('email', 'name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Info', {'fields': ('name', 'role', 'image')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2', 'name', 'role')}),
    )


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'used')
    list_filter = ('created_at', 'used')
