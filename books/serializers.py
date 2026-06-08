from rest_framework import serializers
from .models import Book
from core.models import SchoolClass


class BookSerializer(serializers.ModelSerializer):
    className = serializers.CharField(source='school_class.name', read_only=True)
    classId = serializers.UUIDField(source='school_class_id', required=False, allow_null=True)

    class Meta:
        model = Book
        fields = ['id', 'name', 'className', 'classId', 'publication', 'mrp', 'discounted', 'sell']
        read_only_fields = ['id', 'className']
