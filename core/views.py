from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction
from django.db.models import Count, Q, Subquery, OuterRef
from .models import SchoolClass, Subject, AcademicYear, SchoolSetting, AuditLog, Category
from students.models import Student
from books.models import Book
from .serializers import (
    SchoolClassSerializer, SchoolClassReorderSerializer,
    SubjectSerializer, AcademicYearSerializer,
    SchoolSettingSerializer, AuditLogSerializer, CategorySerializer,
    PromoteAllSerializer,
)
from accounts.permissions import require_permission


class ClassViewSet(viewsets.ModelViewSet):
    queryset = SchoolClass.objects.annotate(
        student_count=Subquery(
            Student.objects.filter(school_class=OuterRef('pk'), deleted_at__isnull=True)
            .order_by().values('school_class').annotate(c=Count('pk')).values('c')
        ),
        book_count=Subquery(
            Book.objects.filter(school_class=OuterRef('pk'))
            .order_by().values('school_class').annotate(c=Count('pk')).values('c')
        ),
        subject_count=Subquery(
            Subject.objects.filter(school_class=OuterRef('pk'))
            .order_by().values('school_class').annotate(c=Count('pk')).values('c')
        ),
    )
    serializer_class = SchoolClassSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [require_permission('classes:read')()]
        return [require_permission('classes:write')()]

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        serializer = SchoolClassReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for idx, class_id in enumerate(serializer.validated_data['order']):
            SchoolClass.objects.filter(pk=class_id).update(order=idx)
        return Response({'status': 'ok'})

    @action(detail=False, methods=['post'])
    def promote_all(self, request):
        serializer = PromoteAllSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        with db_transaction.atomic():
            # Backward-compatible: simple class-to-class promotion
            if 'from_class_id' in data and 'to_class_id' in data:
                from_id = data['from_class_id']
                to_id = data['to_class_id']
                Student.objects.filter(school_class_id=from_id, deleted_at__isnull=True)\
                    .update(school_class_id=to_id)
                return Response({'status': 'ok'})

            # Full end-of-year promotion
            target_year_name = data.get('targetYearName')
            target_academic_year_id = data.get('targetAcademicYearId')
            is_dry_run = request.query_params.get('dryRun') == 'true'

            classes = list(SchoolClass.objects.order_by('order', 'name'))
            promoted = []
            graduated = []
            classes_created = []

            for i, cls in enumerate(classes):
                is_last = i == len(classes) - 1

                if is_last:
                    graduating = Student.objects.filter(
                        school_class=cls, deleted_at__isnull=True,
                        graduated_at__isnull=True
                    )
                    count = graduating.count()
                    if count:
                        graduated.append({'from': cls.name, 'count': count})
                        if not is_dry_run:
                            graduating.update(
                                graduated_at=now,
                                school_class=None
                            )
                    continue

                next_class = classes[i + 1]
                promoting = Student.objects.filter(
                    school_class=cls, deleted_at__isnull=True,
                    graduated_at__isnull=True
                )
                count = promoting.count()
                if not count:
                    continue
                promoted.append({
                    'from': cls.name,
                    'to': next_class.name,
                    'count': count,
                })
                if not is_dry_run:
                    promoting.update(school_class=next_class)

            # Update session for all students
            if target_year_name and not is_dry_run:
                Student.objects.filter(deleted_at__isnull=True).update(
                    session=target_year_name
                )

            return Response({
                'promoted': promoted,
                'graduated': graduated,
                'classesCreated': classes_created,
            })


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.select_related('school_class').all()
    serializer_class = SubjectSerializer
    filterset_fields = ['school_class_id']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [require_permission('subjects:read')()]
        if self.action == 'destroy':
            return [require_permission('subjects:admin')()]
        return [require_permission('subjects:write')()]

    def get_queryset(self):
        qs = super().get_queryset()
        class_id = self.kwargs.get('class_id') or self.request.query_params.get('class_id')
        if class_id:
            qs = qs.filter(school_class_id=class_id)
        return qs

    def perform_create(self, serializer):
        class_id = self.kwargs.get('class_id')
        if class_id:
            max_order = Subject.objects.filter(school_class_id=class_id).order_by('-order').values_list('order', flat=True).first() or 0
            serializer.save(school_class_id=class_id, order=max_order + 1)
        else:
            serializer.save()


class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer

    def get_permissions(
self):
        if self.action in ['list', 'retrieve']:
            return [require_permission('academic-years:read')()]
        return [require_permission('academic-years:write')()]

    def perform_create(self, serializer):
        if serializer.validated_data.get('is_active'):
            AcademicYear.objects.filter(is_active=True).update(is_active=False)
        serializer.save()

    def perform_update(self, serializer):
        if serializer.validated_data.get('is_active'):
            AcademicYear.objects.filter(is_active=True).update(is_active=False)
        serializer.save()


class SettingView(generics.RetrieveUpdateAPIView):
    queryset = SchoolSetting.objects.all()
    serializer_class = SchoolSettingSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [require_permission('classes:read')()]
        return [require_permission('users:write')()]

    def get_object(self):
        key = self.request.query_params.get('key')
        if key:
            from django.shortcuts import get_object_or_404
            return get_object_or_404(SchoolSetting, key=key)
        obj = SchoolSetting.objects.first()
        if not obj:
            from rest_framework.exceptions import NotFound
            raise NotFound('No settings found')
        return obj


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [require_permission('audit:read')]
    filterset_fields = ['action', 'entity_type', 'user_id']
    search_fields = ['entity_id', 'details']
    ordering_fields = ['created_at']


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [require_permission('finance:read')()]
        return [require_permission('finance:write')()]

    def get_queryset(self):
        qs = super().get_queryset()
        type_filter = self.request.query_params.get('type')
        if type_filter:
            qs = qs.filter(type=type_filter.upper())
        return qs


class DashboardSummaryView(generics.GenericAPIView):
    permission_classes = [require_permission('students:read')]

    def get(self, request):
        from students.models import Student
        from teachers.models import Teacher
        from staff.models import Staff
        from .models import SchoolClass
        from books.models import Book

        return Response({
            'studentCount': Student.objects.filter(deleted_at__isnull=True).count(),
            'teacherCount': Teacher.objects.filter(deleted_at__isnull=True).count(),
            'staffCount': Staff.objects.filter(deleted_at__isnull=True).count(),
            'classCount': SchoolClass.objects.count(),
            'bookCount': Book.objects.count(),
        })


class SetupStatusView(generics.GenericAPIView):
    permission_classes = []

    def get(self, request):
        from accounts.models import User
        has_users = User.objects.exists()
        return Response({
            'initialized': has_users,
        })


class SetupInitView(generics.GenericAPIView):
    permission_classes = []

    def post(self, request):
        from django.db import transaction
        from accounts.models import User
        from accounts.serializers import RegisterSerializer
        with transaction.atomic():
            if User.objects.select_for_update().exists():
                return Response({'error': 'Setup already completed. Use normal registration.'}, status=403)
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            user.role = 'admin'
            user.email_verified = True
            user.save(update_fields=['role', 'email_verified'])
        return Response({
            'user': {'id': str(user.id), 'name': user.name, 'email': user.email, 'role': user.role}
        })

