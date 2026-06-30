from rest_framework import serializers
from .models import RoutineTemplate, LessonPlan, Homework, Diary, ExamRoutine


class RoutineTemplateSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    class_name = serializers.CharField(source='school_class.name', read_only=True)

    class Meta:
        model = RoutineTemplate
        fields = [
            'id', 'school_class', 'class_name', 'section',
            'day', 'period_number', 'subject', 'subject_name',
            'teacher', 'teacher_name', 'created_at',
        ]


class LessonPlanSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='routine_template.subject.name', read_only=True)
    day = serializers.CharField(source='routine_template.day', read_only=True)
    period_number = serializers.IntegerField(source='routine_template.period_number', read_only=True)

    class Meta:
        model = LessonPlan
        fields = [
            'id', 'routine_template', 'week_start', 'topic',
            'learning_objectives', 'activities', 'materials',
            'assessment', 'remarks', 'completed',
            'subject_name', 'day', 'period_number',
            'created_at', 'updated_at',
        ]


class HomeworkSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    class_name = serializers.CharField(source='school_class.name', read_only=True)

    class Meta:
        model = Homework
        fields = [
            'id', 'school_class', 'class_name', 'section',
            'subject', 'subject_name', 'teacher', 'teacher_name',
            'date', 'topic', 'description', 'due_date',
            'attachment', 'published',
            'created_at', 'updated_at',
        ]


class DiarySerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    class_name = serializers.CharField(source='school_class.name', read_only=True)

    class Meta:
        model = Diary
        fields = [
            'id', 'school_class', 'class_name', 'section',
            'subject', 'subject_name', 'teacher', 'teacher_name',
            'date', 'topic', 'activities', 'remarks',
            'attachment', 'created_at', 'updated_at',
        ]


class ExamRoutineSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    class_name = serializers.CharField(source='school_class.name', read_only=True)

    class Meta:
        model = ExamRoutine
        fields = [
            'id', 'exam_name', 'school_class', 'class_name', 'section',
            'subject', 'subject_name', 'date', 'start_time', 'end_time', 'room',
            'created_at',
        ]


class PeriodSettingSerializer(serializers.Serializer):
    period_number = serializers.IntegerField()
    start_time = serializers.CharField(max_length=10)
    end_time = serializers.CharField(max_length=10)
