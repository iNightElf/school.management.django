from rest_framework import serializers
from .models import Teacher
from core.supabase_storage import get_signed_url


class TeacherSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='designation', read_only=True)
    hasPhoto = serializers.SerializerMethodField()
    photoUrl = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Teacher
        fields = ['id', 'name', 'contact', 'email', 'role', 'hasPhoto', 'photoUrl', 'createdAt']
        read_only_fields = ['id', 'createdAt']

    def get_hasPhoto(self, obj):
        return bool(obj.photo_path)

    def get_photoUrl(self, obj):
        if obj.photo_path:
            from django.core import signing
            token = signing.dumps({'id': str(obj.id)}, salt='photo-access')
            path = f"/api/teachers/{obj.id}/photo/?token={token}"
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(path)
            return path
        return None
