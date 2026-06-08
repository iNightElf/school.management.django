from rest_framework import serializers
from .models import SchoolClass, Subject, AcademicYear, SchoolSetting, AuditLog, Category, StudentIdCounter


class SchoolClassSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    studentCount = serializers.IntegerField(source='student_count', read_only=True)
    bookCount = serializers.IntegerField(source='book_count', read_only=True)
    subjectCount = serializers.IntegerField(source='subject_count', read_only=True)

    class Meta:
        model = SchoolClass
        fields = ['id', 'name', 'order', 'createdAt', 'studentCount', 'bookCount', 'subjectCount']


class SchoolClassReorderSerializer(serializers.Serializer):
    order = serializers.ListField(child=serializers.UUIDField())


class SubjectSerializer(serializers.ModelSerializer):
    fullMarks = serializers.IntegerField(source='full_marks')
    classId = serializers.UUIDField(source='school_class_id', read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'name', 'fullMarks', 'classId', 'order']


class AcademicYearSerializer(serializers.ModelSerializer):
    isActive = serializers.BooleanField(source='is_active', required=False)
    startDate = serializers.DateField(source='start_date', required=False, allow_null=True)
    endDate = serializers.DateField(source='end_date', required=False, allow_null=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = AcademicYear
        fields = ['id', 'name', 'isActive', 'startDate', 'endDate', 'createdAt']

    def validate_isActive(self, value):
        return value


class SchoolSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolSetting
        fields = ['id', 'key', 'value']


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'user_id', 'action', 'entity_type', 'entity_id', 'details', 'created_at']
        read_only_fields = ['created_at']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'type']


class PromoteAllSerializer(serializers.Serializer):
    from_class_id = serializers.UUIDField(required=False)
    to_class_id = serializers.UUIDField(required=False)
    targetYearName = serializers.CharField(required=False)
    targetAcademicYearId = serializers.UUIDField(required=False)
