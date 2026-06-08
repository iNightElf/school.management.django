from rest_framework import serializers
from .models import Staff
from core.supabase_storage import get_signed_url


class StaffSerializer(serializers.ModelSerializer):
    designation = serializers.CharField(source='role', read_only=True)
    hasPhoto = serializers.SerializerMethodField()
    photoUrl = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Staff
        fields = ['id', 'name', 'role', 'contact', 'email', 'designation', 'hasPhoto', 'photoUrl', 'createdAt']
        read_only_fields = ['id', 'createdAt', 'designation']

    def get_hasPhoto(self, obj):
        return bool(obj.photo_path)

    def get_photoUrl(self, obj):
        if obj.photo_path:
            from django.core import signing
            token = signing.dumps({'id': str(obj.id)}, salt='photo-access')
            path = f"/api/staff/{obj.id}/photo/?token={token}"
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(path)
            return path
        return None
