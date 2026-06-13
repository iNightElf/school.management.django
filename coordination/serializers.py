from rest_framework import serializers
from core.camelcase import CamelCaseModelSerializer
from .models import (
    Alert, Intervention, ParentCommunication,
    TeacherWeeklyReport, ClassTest, ClassTestMark, CoordinatorTask,
)


class AlertSerializer(CamelCaseModelSerializer):
    studentName = serializers.CharField(source='student.name', read_only=True)
    className = serializers.CharField(source='student.school_class.name', read_only=True, default='')
    createdByName = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            'id', 'student', 'studentName', 'className', 'alertType', 'title',
            'description', 'status', 'severity', 'createdBy', 'createdByName',
            'createdAt', 'resolvedAt',
        ]
        read_only_fields = ['id', 'createdBy', 'createdAt', 'resolvedAt']

    def get_createdByName(self, obj):
        if obj.created_by:
            return getattr(obj.created_by, 'name', None) or obj.created_by.email
        return None

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class InterventionSerializer(CamelCaseModelSerializer):
    alertTitle = serializers.CharField(source='alert.title', read_only=True)
    studentName = serializers.SerializerMethodField()
    createdByName = serializers.SerializerMethodField()

    class Meta:
        model = Intervention
        fields = [
            'id', 'alert', 'alertTitle', 'studentName', 'actionTaken',
            'followupDate', 'remarks', 'status', 'createdBy', 'createdByName',
            'createdAt',
        ]
        read_only_fields = ['id', 'createdBy', 'createdAt']

    def get_studentName(self, obj):
        return obj.alert.student.name if obj.alert and obj.alert.student else None

    def get_createdByName(self, obj):
        if obj.created_by:
            return getattr(obj.created_by, 'name', None) or obj.created_by.email
        return None

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ParentCommunicationSerializer(CamelCaseModelSerializer):
    studentName = serializers.CharField(source='student.name', read_only=True)
    className = serializers.CharField(source='student.school_class.name', read_only=True, default='')
    createdByName = serializers.SerializerMethodField()

    class Meta:
        model = ParentCommunication
        fields = [
            'id', 'student', 'studentName', 'className', 'communicationType',
            'notes', 'followupDate', 'createdBy', 'createdByName', 'createdAt',
        ]
        read_only_fields = ['id', 'createdBy', 'createdAt']

    def get_createdByName(self, obj):
        if obj.created_by:
            return getattr(obj.created_by, 'name', None) or obj.created_by.email
        return None

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TeacherWeeklyReportSerializer(CamelCaseModelSerializer):
    teacherName = serializers.SerializerMethodField()
    className = serializers.SerializerMethodField()

    class Meta:
        model = TeacherWeeklyReport
        fields = [
            'id', 'classTeacher', 'teacherName', 'className', 'weekStartDate',
            'attendanceNotes', 'academicsNotes', 'behaviorNotes',
            'parentIssuesNotes', 'recognitionNotes', 'status',
            'createdAt', 'submittedAt',
        ]
        read_only_fields = ['id', 'createdAt', 'submittedAt']

    def get_teacherName(self, obj):
        return obj.class_teacher.teacher.name if obj.class_teacher and obj.class_teacher.teacher else None

    def get_className(self, obj):
        return obj.class_teacher.school_class.name if obj.class_teacher and obj.class_teacher.school_class else None

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ClassTestMarkSerializer(CamelCaseModelSerializer):
    studentName = serializers.CharField(source='student.name', read_only=True)
    roll = serializers.CharField(source='student.roll', read_only=True)
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = ClassTestMark
        fields = [
            'id', 'classTest', 'student', 'studentName', 'roll',
            'marksObtained', 'percentage', 'createdAt',
        ]
        read_only_fields = ['id', 'createdAt']

    def get_percentage(self, obj):
        if obj.class_test and obj.class_test.total_marks:
            return round(obj.marks_obtained / obj.class_test.total_marks * 100, 1)
        return 0


class ClassTestSerializer(CamelCaseModelSerializer):
    className = serializers.CharField(source='school_class.name', read_only=True)
    subjectName = serializers.CharField(source='subject.name', read_only=True)
    createdByName = serializers.SerializerMethodField()
    marks = ClassTestMarkSerializer(many=True, read_only=True)
    averageMarks = serializers.SerializerMethodField()
    highestMarks = serializers.SerializerMethodField()
    lowestMarks = serializers.SerializerMethodField()
    passRate = serializers.SerializerMethodField()

    class Meta:
        model = ClassTest
        fields = [
            'id', 'schoolClass', 'className', 'subject', 'subjectName',
            'term', 'testName', 'testDate', 'totalMarks', 'createdBy', 'createdByName',
            'createdAt', 'marks', 'averageMarks', 'highestMarks',
            'lowestMarks', 'passRate',
        ]
        read_only_fields = ['id', 'createdBy', 'createdAt']

    def get_createdByName(self, obj):
        if obj.created_by:
            return getattr(obj.created_by, 'name', None) or obj.created_by.email
        return None

    def get_averageMarks(self, obj):
        marks_list = list(obj.marks.values_list('marks_obtained', flat=True))
        if not marks_list:
            return 0
        return round(sum(marks_list) / len(marks_list), 1)

    def get_highestMarks(self, obj):
        marks_list = list(obj.marks.values_list('marks_obtained', flat=True))
        return max(marks_list) if marks_list else 0

    def get_lowestMarks(self, obj):
        marks_list = list(obj.marks.values_list('marks_obtained', flat=True))
        return min(marks_list) if marks_list else 0

    def get_passRate(self, obj):
        total = obj.marks.count()
        if total == 0:
            return 0
        passed = obj.marks.filter(marks_obtained__gte=obj.total_marks * 0.4).count()
        return round(passed / total * 100, 1)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CoordinatorTaskSerializer(CamelCaseModelSerializer):
    assignedToName = serializers.SerializerMethodField()
    relatedAlertTitle = serializers.SerializerMethodField()
    createdByName = serializers.SerializerMethodField()

    class Meta:
        model = CoordinatorTask
        fields = [
            'id', 'title', 'description', 'dueDate', 'status', 'priority',
            'assignedTo', 'assignedToName', 'relatedAlert', 'relatedAlertTitle',
            'createdBy', 'createdByName', 'createdAt', 'completedAt',
        ]
        read_only_fields = ['id', 'createdBy', 'createdAt', 'completedAt']

    def get_assignedToName(self, obj):
        if obj.assigned_to:
            return getattr(obj.assigned_to, 'name', None) or obj.assigned_to.email
        return None

    def get_relatedAlertTitle(self, obj):
        return obj.related_alert.title if obj.related_alert else None

    def get_createdByName(self, obj):
        if obj.created_by:
            return getattr(obj.created_by, 'name', None) or obj.created_by.email
        return None

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
