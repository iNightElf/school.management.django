from django.contrib import admin
from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_class', 'publication', 'mrp', 'sell')
    list_filter = ('school_class',)
    search_fields = ('name', 'publication')
    readonly_fields = ('id',)
