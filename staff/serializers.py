from rest_framework import serializers
from .models import Staff
from core.mixins import PhotoUrlMixin


class StaffSerializer(PhotoUrlMixin, serializers.ModelSerializer):
    photo_url_prefix = 'staff'
    designation = serializers.CharField(source='role', read_only=True)
    hasPhoto = serializers.SerializerMethodField()
    photoUrl = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Staff
        fields = ['id', 'name', 'role', 'contact', 'email', 'designation', 'hasPhoto', 'photoUrl', 'createdAt']
        read_only_fields = ['id', 'createdAt', 'designation']
