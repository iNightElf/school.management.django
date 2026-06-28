from django.contrib import admin
from .models import ParentStudentLink, PushSubscription, NotificationLog, Announcement


class ParentStudentLinkInline(admin.TabularInline):
    model = ParentStudentLink
    extra = 1
    autocomplete_fields = ['student']
    fk_name = 'parent'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parent':
            kwargs['queryset'] = db_field.related_model.objects.filter(role='parent')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ParentStudentLink)
class ParentStudentLinkAdmin(admin.ModelAdmin):
    list_display = ('parent', 'student', 'created_at')
    list_filter = ('parent__role', 'created_at')
    search_fields = ('parent__name', 'parent__email', 'student__name')
    autocomplete_fields = ['parent', 'student']


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'user_agent')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__name')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'title', 'sent_at', 'error')
    list_filter = ('event_type', 'sent_at')
    search_fields = ('user__email', 'user__name', 'title')
    readonly_fields = ('user', 'event_type', 'title', 'body', 'payload', 'sent_at', 'error')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'body', 'author__name')
    readonly_fields = ('created_at',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)
        if not change:
            from .services import notify_all_parents
            notify_all_parents(obj.title, obj.body)
