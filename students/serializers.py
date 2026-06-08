from rest_framework import serializers
from django.db import transaction as db_transaction
from .models import Student
from core.models import StudentIdCounter


class StudentSerializer(serializers.ModelSerializer):
    classId = serializers.UUIDField(source='school_class_id', read_only=True, allow_null=True)
    schoolClass = serializers.UUIDField(source='school_class', required=False, allow_null=True)
    klass = serializers.CharField(source='school_class.name', read_only=True, allow_null=True)
    studentId = serializers.CharField(source='student_id', read_only=True)
    fatherName = serializers.CharField(source='father_name', read_only=True, allow_null=True)
    motherName = serializers.CharField(source='mother_name', read_only=True, allow_null=True)
    hasPhoto = serializers.SerializerMethodField()
    hasGraduated = serializers.SerializerMethodField()
    photoUrl = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'studentId', 'schoolClass', 'classId', 'klass', 'roll',
            'session', 'name', 'fatherName', 'motherName', 'contact',
            'hasPhoto', 'hasGraduated', 'photoUrl', 'createdAt',
        ]
        read_only_fields = ['id', 'studentId', 'createdAt']

    def get_hasPhoto(self, obj):
        return bool(obj.photo_path)

    def get_hasGraduated(self, obj):
        return obj.graduated_at is not None

    def get_photoUrl(self, obj):
        if obj.photo_path:
            from django.core import signing
            token = signing.dumps({'id': str(obj.id)}, salt='photo-access')
            path = f"/api/students/{obj.id}/photo/?token={token}"
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(path)
            return path
        return None

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['class'] = ret.pop('klass', None)
        return ret

    def create(self, validated_data):
        with db_transaction.atomic():
            counter, _ = StudentIdCounter.objects.select_for_update().get_or_create(
                id='singleton',
                defaults={'prefix': 'S', 'next_value': 1, 'pad_length': 6}
            )
            student_id = f"{counter.prefix}{str(counter.next_value).zfill(counter.pad_length)}"
            validated_data['student_id'] = student_id
            counter.next_value += 1
            counter.save(update_fields=['next_value'])
        return super().create(validated_data)


class ImportSerializer(serializers.Serializer):
    file = serializers.FileField()
