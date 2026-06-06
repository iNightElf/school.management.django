from rest_framework import serializers
from .models import Book


class BookSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='school_class.name', read_only=True)

    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ['id']
