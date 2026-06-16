from django.contrib import admin
from django import forms
from django.contrib.auth.hashers import make_password
from .models import Teacher, ClassTeacher, TeacherSubject


class TeacherAdminForm(forms.ModelForm):
    pin = forms.CharField(
        label='Mobile PIN',
        widget=forms.PasswordInput(render_value=True),
        required=False,
        help_text='6-digit PIN for mobile attendance app. Leave blank to keep current.',
        max_length=6,
    )

    class Meta:
        model = Teacher
        fields = '__all__'

    def clean_pin(self):
        pin = self.cleaned_data.get('pin')
        if pin and (not pin.isdigit() or len(pin) != 6):
            raise forms.ValidationError('PIN must be exactly 6 digits')
        return pin

    def save(self, commit=True):
        pin = self.cleaned_data.get('pin')
        if pin:
            self.instance.pin = make_password(pin)
        return super().save(commit)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    form = TeacherAdminForm
    list_display = ('name', 'designation', 'email', 'user', 'contact', 'pin_set', 'created_at')
    list_filter = ('designation',)
    search_fields = ('name', 'email', 'contact')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        (None, {'fields': ('name', 'designation', 'email', 'contact', 'user')}),
        ('Mobile Access', {'fields': ('pin',), 'classes': ('collapse',)}),
        ('Metadata', {'fields': ('id', 'created_at', 'deleted_at')}),
    )

    @admin.display(boolean=True, description='Has PIN')
    def pin_set(self, obj):
        return bool(obj.pin)


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
