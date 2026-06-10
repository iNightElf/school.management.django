from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from django.utils import timezone
from .models import Student
from .serializers import StudentSerializer
from accounts.permissions import require_permission, can_manage_students, is_admin_or_superuser
from core.mixins import PhotoHandleMixin
from core.audit import log_audit


class StudentViewSet(PhotoHandleMixin, viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    photo_prefix = 'students'
    filterset_fields = ['school_class_id', 'session']

    def get_permissions(self):
        if self.action == 'photo':
            from rest_framework.permissions import AllowAny
            return [AllowAny()]
        if self.action in ['list', 'retrieve', 'class_results']:
            return [require_permission('students:read')()]
        return [require_permission('students:write')()]

    def get_queryset(self):
        qs = Student.objects.select_related('school_class').all()
        show_archived = self.request.query_params.get('archived', 'false').lower() == 'true'
        search = self.request.query_params.get('search')
        class_id = self.request.query_params.get('class_id')

        if not show_archived:
            qs = qs.filter(deleted_at__isnull=True)
        if class_id:
            qs = qs.filter(school_class_id=class_id)
        if search:
            qs = qs.filter(
                models.Q(name__icontains=search) |
                models.Q(student_id__icontains=search) |
                models.Q(roll__icontains=search)
            )
        return qs

    def perform_create(self, serializer):
        school_class = serializer.validated_data.get('school_class')
        if school_class and not is_admin_or_superuser(self.request.user):
            if not can_manage_students(self.request.user, school_class.id):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You are not the class teacher of this class.')
        obj = serializer.save()
        log_audit('create', 'student', entity_id=obj.pk, request=self.request)

    def perform_destroy(self, instance):
        if instance.school_class_id and not is_admin_or_superuser(self.request.user):
            if not can_manage_students(self.request.user, instance.school_class_id):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You are not the class teacher of this class.')
        entity_id = str(instance.pk)
        super().perform_destroy(instance)
        log_audit('delete', 'student', entity_id=entity_id, request=self.request)

    @action(detail=True, methods=['post'])
    def graduate(self, request, pk=None):
        student = self.get_object()
        if student.school_class_id and not is_admin_or_superuser(request.user):
            if not can_manage_students(request.user, student.school_class_id):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You are not the class teacher of this class.')
        student.graduated_at = timezone.now()
        student.save(update_fields=['graduated_at'])
        log_audit('graduate', 'student', entity_id=student.pk, request=request)
        return Response(StudentSerializer(student).data)

    @action(detail=True, methods=['post'])
    def ungraduate(self, request, pk=None):
        student = self.get_object()
        if student.school_class_id and not is_admin_or_superuser(request.user):
            if not can_manage_students(request.user, student.school_class_id):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You are not the class teacher of this class.')
        student.graduated_at = None
        student.save(update_fields=['graduated_at'])
        log_audit('ungraduate', 'student', entity_id=student.pk, request=request)
        return Response(StudentSerializer(student).data)

    @action(detail=False, methods=['post'])
    def import_students(self, request):
        from .serializers import ImportSerializer
        import_serializer = ImportSerializer(data=request.data)
        import_serializer.is_valid(raise_exception=True)
        file = import_serializer.validated_data['file']
        return Response({'status': 'not_implemented', 'detail': 'Import from file not yet implemented'})

    @action(detail=False, methods=['post'])
    def graduate_class(self, request):
        class_id = request.data.get('class_id')
        if not class_id:
            return Response({'error': 'class_id required'}, status=400)
        if not is_admin_or_superuser(request.user):
            if not can_manage_students(request.user, class_id):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You are not the class teacher of this class.')
        count = Student.objects.filter(
            school_class_id=class_id, deleted_at__isnull=True
        ).update(graduated_at=timezone.now())
        log_audit('graduate_class', 'student', details={'class_id': class_id, 'count': count}, request=request)
        return Response({'status': 'ok', 'count': count})
