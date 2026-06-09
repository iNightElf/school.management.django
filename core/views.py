import logging
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

logger = logging.getLogger(__name__)


def _parse_student_roll(student_id):
    """Parse r{year}{classNum}{roll} format. Returns (year, class_num, roll) or None."""
    if not student_id or not isinstance(student_id, str):
        return None
    s = student_id.strip()
    if not s.startswith('r') or len(s) < 7:
        return None
    body = s[1:]
    if len(body) == 7:
        year = body[:4]
        class_num = int(body[4])
        roll = body[5:7]
    elif len(body) == 8:
        year = body[:4]
        class_num = int(body[4:6])
        roll = body[6:8]
    else:
        return None
    return year, class_num, roll


def _generate_student_roll(year, class_num, roll):
    """Generate r{year}{classNum:02d}{roll} format."""
    return f'r{year}{class_num:02d}{roll}'


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
        is_dry_run = request.query_params.get('dryRun') == 'true'

        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)

            # Backward-compatible: simple class-to-class promotion
            if 'from_class_id' in data and 'to_class_id' in data:
                from_id = data['from_class_id']
                to_id = data['to_class_id']
                if not is_dry_run:
                    Student.objects.filter(
                        school_class_id=from_id, deleted_at__isnull=True
                    ).update(school_class_id=to_id)
                from_name = SchoolClass.objects.filter(id=from_id).values_list('name', flat=True).first() or str(from_id)
                to_name = SchoolClass.objects.filter(id=to_id).values_list('name', flat=True).first() or str(to_id)
                count = Student.objects.filter(
                    school_class_id=from_id, deleted_at__isnull=True
                ).count()
                return Response({
                    'promoted': [{'from': from_name, 'to': to_name, 'count': count}],
                    'graduated': [],
                    'classesCreated': [],
                })

            # Full end-of-year promotion
            target_year_name = data.get('targetYearName')
            target_year = int(target_year_name) if target_year_name and target_year_name.isdigit() else None

            MAX_CLASS_ORDER = 12  # Class Ten = order 12, classNum 13

            CLASS_NAMES = {
                8: 'Class Six', 9: 'Class Seven', 10: 'Class Eight',
                11: 'Class Nine', 12: 'Class Ten',
            }

            classes = list(SchoolClass.objects.order_by('order', 'name'))
            if not classes:
                return Response(
                    {'error': 'No classes found. Create classes before promoting.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            promoted = []
            graduated = []
            classes_created = []

            # Build map of class order → class object
            class_by_order = {cls.order: cls for cls in classes}
            max_order = max(c.order for c in classes) if classes else 0

            # Collect all moves and new rolls from ORIGINAL state (no cascade)
            moves = []
            grads = []
            new_rolls = {}

            for cls in classes:
                students = list(Student.objects.filter(
                    school_class=cls, deleted_at__isnull=True,
                    graduated_at__isnull=True,
                ))
                if not students:
                    continue

                next_order = cls.order + 1

                if next_order > MAX_CLASS_ORDER:
                    grads.append((cls, students))
                    continue

                next_class = class_by_order.get(next_order)
                if not next_class and not is_dry_run:
                    name = CLASS_NAMES.get(next_order, f'Class {next_order}')
                    next_class = SchoolClass.objects.create(name=name, order=next_order)
                    class_by_order[next_order] = next_class
                    classes_created.append(name)
                elif not next_class:
                    name = CLASS_NAMES.get(next_order, f'Class {next_order}')
                    classes_created.append(name)

                promoted.append({
                    'from': cls.name,
                    'to': next_class.name if next_class else CLASS_NAMES.get(next_order, f'Class {next_order}'),
                    'count': len(students),
                })
                moves.append((cls, next_class, students))

                # Compute new roll numbers
                for s in students:
                    parsed = _parse_student_roll(s.student_id)
                    if parsed and target_year:
                        old_year, old_class_num, old_roll = parsed
                        new_class_num = old_class_num + 1
                        new_id = _generate_student_roll(target_year, new_class_num, old_roll)
                        new_rolls[s.id] = (new_id, next_order)

            # Graduation roll numbers
            for cls, students in grads:
                graduation_class_num = cls.order + 1
                for s in students:
                    parsed = _parse_student_roll(s.student_id)
                    if parsed and target_year:
                        _, _, old_roll = parsed
                        new_id = _generate_student_roll(target_year, graduation_class_num, old_roll)
                        new_rolls[s.id] = (new_id, cls.order)

            # Apply all changes
            if not is_dry_run:
                # Move students to next classes
                for cls, next_class, students in moves:
                    for s in students:
                        s.school_class = next_class
                    Student.objects.bulk_update(students, ['school_class'])

                # Graduate students
                for cls, students in grads:
                    for s in students:
                        s.graduated_at = now
                        s.school_class = None
                    Student.objects.bulk_update(students, ['graduated_at', 'school_class'])

                # Update roll numbers
                if new_rolls:
                    students_to_update = Student.objects.filter(id__in=new_rolls.keys())
                    for s in students_to_update:
                        new_id, _ = new_rolls[s.id]
                        s.student_id = new_id
                    Student.objects.bulk_update(students_to_update, ['student_id'])

                # Update session for all students
                if target_year_name:
                    Student.objects.filter(deleted_at__isnull=True).update(
                        session=target_year_name,
                    )

            return Response({
                'promoted': promoted,
                'graduated': [{'from': cls.name, 'count': len(students)} for cls, students in grads],
                'classesCreated': classes_created,
            })

        except Exception as e:
            logger.exception('promote_all failed')
            return Response(
                {'error': f'Promotion failed: {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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


class SettingView(generics.GenericAPIView):
    queryset = SchoolSetting.objects.all()
    serializer_class = SchoolSettingSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [require_permission('classes:read')()]
        return [require_permission('users:write')()]

    def get(self, request):
        key = request.query_params.get('key')
        if key:
            from django.shortcuts import get_object_or_404
            obj = get_object_or_404(SchoolSetting, key=key)
            return Response(SchoolSettingSerializer(obj).data)
        settings = {s.key: s.value for s in SchoolSetting.objects.all()}
        if not settings:
            settings = {
                'school_name': 'AL RAWA English School',
                'address': '',
                'phone': '',
                'email': '',
                'website': '',
            }
        return Response(settings)

    def put(self, request):
        data = request.data
        for key, value in data.items():
            if key == 'id':
                continue
            SchoolSetting.objects.update_or_create(
                key=key,
                defaults={'value': str(value) if value is not None else ''},
            )
        settings = {s.key: s.value for s in SchoolSetting.objects.all()}
        return Response(settings)


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

