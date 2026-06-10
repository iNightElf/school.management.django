from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Teacher, ClassTeacher, TeacherSubject
from .serializers import (
    TeacherSerializer, ClassTeacherSerializer, TeacherSubjectSerializer,
    AssignClassTeacherSerializer, RemoveClassTeacherSerializer,
    AssignSubjectSerializer, RemoveSubjectSerializer,
)
from accounts.permissions import require_permission
from core.mixins import PhotoHandleMixin
from core.audit import log_audit
from core.models import SchoolClass, Subject


class TeacherViewSet(PhotoHandleMixin, viewsets.ModelViewSet):
    serializer_class = TeacherSerializer
    photo_prefix = 'teachers'
    filterset_fields = ['designation']

    def get_permissions(self):
        if self.action == 'photo':
            from rest_framework.permissions import AllowAny
            return [AllowAny()]
        if self.action in ['list', 'retrieve']:
            return [require_permission('teachers:read')()]
        return [require_permission('teachers:write')()]

    def get_queryset(self):
        qs = Teacher.objects.all()
        show_deleted = self.request.query_params.get('deleted', 'false').lower() == 'true'
        if not show_deleted:
            qs = qs.filter(deleted_at__isnull=True)
        return qs.select_related('user').prefetch_related(
            'class_teacher_of__school_class',
            'subject_assignments__subject',
            'subject_assignments__school_class',
        )

    @action(detail=False, methods=['post'])
    def import_teachers(self, request):
        return Response({'status': 'not_implemented', 'detail': 'Import from file not yet implemented'})

    @action(detail=True, methods=['get', 'post'])
    def class_teacher(self, request, pk=None):
        teacher = self.get_object()

        if request.method == 'GET':
            assignments = teacher.class_teacher_of.select_related('school_class').all()
            return Response(ClassTeacherSerializer(assignments, many=True).data)

        serializer = AssignClassTeacherSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        school_class = SchoolClass.objects.filter(id=serializer.validated_data['classId']).first()
        if not school_class:
            return Response({'error': 'Class not found'}, status=404)

        _, created = ClassTeacher.objects.get_or_create(
            teacher=teacher, school_class=school_class,
        )
        if not created:
            return Response({'error': 'Already assigned to this class'}, status=400)

        log_audit('assign_class_teacher', 'teacher', entity_id=str(teacher.pk),
                  details={'class_id': str(school_class.pk)}, request=request)
        return Response(
            ClassTeacherSerializer(ClassTeacher.objects.get(teacher=teacher, school_class=school_class)).data,
            status=201,
        )

    @action(detail=True, methods=['post'])
    def remove_class_teacher(self, request, pk=None):
        teacher = self.get_object()
        serializer = RemoveClassTeacherSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        deleted, _ = ClassTeacher.objects.filter(
            teacher=teacher, school_class_id=serializer.validated_data['classId'],
        ).delete()
        if not deleted:
            return Response({'error': 'Not assigned to this class'}, status=404)

        log_audit('remove_class_teacher', 'teacher', entity_id=str(teacher.pk),
                  details={'class_id': serializer.validated_data['classId']}, request=request)
        return Response({'status': 'ok'})

    @action(detail=True, methods=['get', 'post'])
    def subject_assignment(self, request, pk=None):
        teacher = self.get_object()

        if request.method == 'GET':
            assignments = teacher.subject_assignments.select_related('subject', 'school_class').all()
            return Response(TeacherSubjectSerializer(assignments, many=True).data)

        serializer = AssignSubjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject = Subject.objects.filter(id=serializer.validated_data['subjectId']).first()
        school_class = SchoolClass.objects.filter(id=serializer.validated_data['classId']).first()
        if not subject:
            return Response({'error': 'Subject not found'}, status=404)
        if not school_class:
            return Response({'error': 'Class not found'}, status=404)

        _, created = TeacherSubject.objects.get_or_create(
            teacher=teacher, subject=subject, school_class=school_class,
        )
        if not created:
            return Response({'error': 'Already assigned to this subject in this class'}, status=400)

        log_audit('assign_subject', 'teacher', entity_id=str(teacher.pk),
                  details={'subject_id': str(subject.pk), 'class_id': str(school_class.pk)}, request=request)
        return Response(
            TeacherSubjectSerializer(
                TeacherSubject.objects.get(teacher=teacher, subject=subject, school_class=school_class)
            ).data,
            status=201,
        )

    @action(detail=True, methods=['post'])
    def remove_subject(self, request, pk=None):
        teacher = self.get_object()
        serializer = RemoveSubjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        deleted, _ = TeacherSubject.objects.filter(
            teacher=teacher,
            subject_id=serializer.validated_data['subjectId'],
            school_class_id=serializer.validated_data['classId'],
        ).delete()
        if not deleted:
            return Response({'error': 'Not assigned to this subject in this class'}, status=404)

        log_audit('remove_subject', 'teacher', entity_id=str(teacher.pk),
                  details={'subject_id': serializer.validated_data['subjectId'],
                           'class_id': serializer.validated_data['classId']}, request=request)
        return Response({'status': 'ok'})
