from django.db import transaction
from django.db.models import Avg, Max, Min, Count, Q
from django.utils import timezone
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import (
    require_permission, is_admin_or_superuser, is_class_teacher_of,
)
from core.audit import log_audit
from teachers.models import ClassTeacher, TeacherSubject
from .models import (
    Alert, Intervention, ParentCommunication,
    TeacherWeeklyReport, ClassTest, ClassTestMark, CoordinatorTask,
)
from .serializers import (
    AlertSerializer, InterventionSerializer, ParentCommunicationSerializer,
    TeacherWeeklyReportSerializer, ClassTestSerializer, ClassTestMarkSerializer,
    CoordinatorTaskSerializer,
)


def can_enter_class_test(user, class_id, subject_id):
    if is_admin_or_superuser(user):
        return True
    teacher_profile = getattr(user, 'teacher_profile', None)
    if not teacher_profile:
        return False
    return TeacherSubject.objects.filter(
        teacher=teacher_profile, subject_id=subject_id, school_class_id=class_id,
    ).exists()


def can_manage_weekly_report(user, class_teacher_id):
    if is_admin_or_superuser(user):
        return True
    teacher_profile = getattr(user, 'teacher_profile', None)
    if not teacher_profile:
        return False
    return ClassTeacher.objects.filter(
        id=class_teacher_id, teacher=teacher_profile,
    ).exists()


class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    queryset = Alert.objects.select_related('student', 'student__school_class', 'created_by').all()
    filterset_fields = ['alert_type', 'status', 'severity', 'student']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [require_permission('coordinators:read')()]
        return [require_permission('coordinators:write')()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if is_admin_or_superuser(user):
            return qs
        teacher_profile = getattr(user, 'teacher_profile', None)
        if not teacher_profile:
            return qs.none()
        class_ids = ClassTeacher.objects.filter(
            teacher=teacher_profile
        ).values_list('school_class_id', flat=True)
        return qs.filter(student__school_class_id__in=class_ids)

    def perform_create(self, serializer):
        obj = serializer.save()
        log_audit('create', 'alert', obj.pk, request=self.request)

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        obj = serializer.save()
        if old_status != 'resolved' and obj.status == 'resolved':
            obj.resolved_at = timezone.now()
            obj.save(update_fields=['resolved_at'])
        log_audit('update', 'alert', obj.pk, request=self.request)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.save(update_fields=['status', 'resolved_at'])
        log_audit('resolve', 'alert', alert.pk, request=request)
        return Response(AlertSerializer(alert).data)


class InterventionViewSet(viewsets.ModelViewSet):
    serializer_class = InterventionSerializer
    queryset = Intervention.objects.select_related(
        'alert', 'alert__student', 'created_by'
    ).all()
    filterset_fields = ['alert', 'status']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [require_permission('coordinators:read')()]
        return [require_permission('coordinators:write')()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if is_admin_or_superuser(user):
            return qs
        teacher_profile = getattr(user, 'teacher_profile', None)
        if not teacher_profile:
            return qs.none()
        class_ids = ClassTeacher.objects.filter(
            teacher=teacher_profile
        ).values_list('school_class_id', flat=True)
        return qs.filter(alert__student__school_class_id__in=class_ids)

    def perform_create(self, serializer):
        obj = serializer.save()
        log_audit('create', 'intervention', obj.pk, request=self.request)

    def perform_update(self, serializer):
        obj = serializer.save()
        log_audit('update', 'intervention', obj.pk, request=self.request)


class ParentCommunicationViewSet(viewsets.ModelViewSet):
    serializer_class = ParentCommunicationSerializer
    queryset = ParentCommunication.objects.select_related(
        'student', 'student__school_class', 'created_by'
    ).all()
    filterset_fields = ['student', 'communication_type']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [require_permission('coordinators:read')()]
        return [require_permission('coordinators:write')()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if is_admin_or_superuser(user):
            return qs
        teacher_profile = getattr(user, 'teacher_profile', None)
        if not teacher_profile:
            return qs.none()
        class_ids = ClassTeacher.objects.filter(
            teacher=teacher_profile
        ).values_list('school_class_id', flat=True)
        return qs.filter(student__school_class_id__in=class_ids)

    def perform_create(self, serializer):
        obj = serializer.save()
        log_audit('create', 'parent_communication', obj.pk, request=self.request)

    def perform_update(self, serializer):
        obj = serializer.save()
        log_audit('update', 'parent_communication', obj.pk, request=self.request)


class TeacherWeeklyReportViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherWeeklyReportSerializer
    queryset = TeacherWeeklyReport.objects.select_related(
        'class_teacher', 'class_teacher__teacher', 'class_teacher__school_class'
    ).all()
    filterset_fields = ['class_teacher', 'status', 'week_start_date']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [require_permission('coordinators:read')()]
        return [require_permission('coordinators:write')()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if is_admin_or_superuser(user):
            return qs
        teacher_profile = getattr(user, 'teacher_profile', None)
        if not teacher_profile:
            return qs.none()
        return qs.filter(class_teacher__teacher=teacher_profile)

    def perform_create(self, serializer):
        obj = serializer.save()
        log_audit('create', 'teacher_weekly_report', obj.pk, request=self.request)

    def perform_update(self, serializer):
        obj = serializer.save()
        log_audit('update', 'teacher_weekly_report', obj.pk, request=self.request)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        report = self.get_object()
        if not can_manage_weekly_report(request.user, report.class_teacher_id):
            return Response(
                {'detail': 'You can only submit your own reports.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        report.status = 'submitted'
        report.submitted_at = timezone.now()
        report.save(update_fields=['status', 'submitted_at'])
        log_audit('submit', 'teacher_weekly_report', report.pk, request=request)
        return Response(TeacherWeeklyReportSerializer(report).data)


class ClassTestViewSet(viewsets.ModelViewSet):
    serializer_class = ClassTestSerializer
    queryset = ClassTest.objects.select_related(
        'school_class', 'subject', 'created_by'
    ).prefetch_related('marks').all()
    filterset_fields = ['school_class', 'subject']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [require_permission('coordinators:read')()]
        return [require_permission('coordinators:write')()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if is_admin_or_superuser(user):
            return qs
        teacher_profile = getattr(user, 'teacher_profile', None)
        if not teacher_profile:
            return qs.none()
        assigned_class_subjects = TeacherSubject.objects.filter(
            teacher=teacher_profile
        ).values_list('school_class_id', 'subject_id')
        q = Q()
        for class_id, subject_id in assigned_class_subjects:
            q |= Q(school_class_id=class_id, subject_id=subject_id)
        class_ids = ClassTeacher.objects.filter(
            teacher=teacher_profile
        ).values_list('school_class_id', flat=True)
        q |= Q(school_class_id__in=class_ids)
        return qs.filter(q).distinct()

    def perform_create(self, serializer):
        test = serializer.save()
        log_audit('create', 'class_test', test.pk, request=self.request)

    def perform_update(self, serializer):
        obj = serializer.save()
        log_audit('update', 'class_test', obj.pk, request=self.request)

    @action(detail=True, methods=['post'])
    def bulk_marks(self, request, pk=None):
        test = self.get_object()
        if not can_enter_class_test(request.user, test.school_class_id, test.subject_id):
            return Response(
                {'detail': 'You are not assigned to teach this subject in this class.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        marks_data = request.data.get('marks', [])
        if not isinstance(marks_data, list):
            return Response(
                {'detail': 'marks must be a list of { studentId, marksObtained } objects.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        student_ids = [m.get('studentId') for m in marks_data if m.get('studentId')]
        existing_marks = {
            str(m.student_id): m for m in
            ClassTestMark.objects.filter(class_test=test, student_id__in=student_ids)
        }
        created = []
        updated = []
        for item in marks_data:
            student_id = item.get('studentId')
            marks_obtained = item.get('marksObtained')
            if not student_id or marks_obtained is None:
                continue
            try:
                marks_obtained = int(marks_obtained)
            except (TypeError, ValueError):
                continue
            if marks_obtained < 0:
                marks_obtained = 0
            if marks_obtained > test.total_marks:
                marks_obtained = test.total_marks
            if student_id in existing_marks:
                mark_obj = existing_marks[student_id]
                if mark_obj.marks_obtained != marks_obtained:
                    mark_obj.marks_obtained = marks_obtained
                    mark_obj.save(update_fields=['marks_obtained'])
                    updated.append(student_id)
            else:
                ClassTestMark.objects.create(
                    class_test=test,
                    student_id=student_id,
                    marks_obtained=marks_obtained,
                )
                created.append(student_id)
        log_audit(
            'bulk_marks', 'class_test', test.pk,
            details={'created': len(created), 'updated': len(updated)},
            request=request,
        )
        return Response({
            'created': len(created),
            'updated': len(updated),
            'total': test.marks.count(),
        })

    @action(detail=False, methods=['get'])
    def summary(self, request):
        class_id = request.query_params.get('class_id')
        subject_id = request.query_params.get('subject_id')
        qs = self.get_queryset()
        if class_id:
            qs = qs.filter(school_class_id=class_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        tests = qs.annotate(
            avg_marks=Avg('marks__marks_obtained'),
            max_marks=Max('marks__marks_obtained'),
            min_marks=Min('marks__marks_obtained'),
            student_count=Count('marks'),
        ).values(
            'id', 'test_name', 'test_date', 'total_marks',
            'school_class__name', 'subject__name',
            'avg_marks', 'max_marks', 'min_marks', 'student_count',
        )
        return Response(list(tests))

    @action(detail=False, methods=['get'])
    def subject_averages(self, request):
        class_id = request.query_params.get('class_id')
        term = request.query_params.get('term')
        if not class_id or not term:
            return Response(
                {'detail': 'class_id and term are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tests = ClassTest.objects.filter(
            school_class_id=class_id, term=term
        ).select_related('subject')
        subjects_data = {}
        for test in tests:
            subject_id = str(test.subject_id)
            if subject_id not in subjects_data:
                subjects_data[subject_id] = {
                    'subjectId': subject_id,
                    'subjectName': test.subject.name,
                    'totalTests': 0,
                    'normalizedSum': 0.0,
                    'studentCount': 0,
                }
            marks = list(test.marks.values_list('marks_obtained', flat=True))
            subjects_data[subject_id]['totalTests'] += 1
            if marks and test.total_marks:
                for m in marks:
                    subjects_data[subject_id]['normalizedSum'] += (m / test.total_marks) * 10
                    subjects_data[subject_id]['studentCount'] += 1
        result = []
        for data in subjects_data.values():
            count = data['studentCount']
            avg = round(data['normalizedSum'] / count, 2) if count else 0
            result.append({
                'subjectId': data['subjectId'],
                'subjectName': data['subjectName'],
                'totalTests': data['totalTests'],
                'averageOutOf10': avg,
            })
        return Response(result)


class ClassTestMarkViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ClassTestMarkSerializer
    queryset = ClassTestMark.objects.select_related(
        'class_test', 'student'
    ).all()
    filterset_fields = ['class_test', 'student']

    def get_permissions(self):
        return [require_permission('coordinators:read')()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if is_admin_or_superuser(user):
            return qs
        teacher_profile = getattr(user, 'teacher_profile', None)
        if not teacher_profile:
            return qs.none()
        assigned = TeacherSubject.objects.filter(
            teacher=teacher_profile
        ).values_list('school_class_id', 'subject_id')
        q = Q()
        for class_id, subject_id in assigned:
            q |= Q(class_test__school_class_id=class_id, class_test__subject_id=subject_id)
        return qs.filter(q).distinct()


class CoordinatorTaskViewSet(viewsets.ModelViewSet):
    serializer_class = CoordinatorTaskSerializer
    queryset = CoordinatorTask.objects.select_related(
        'assigned_to', 'related_alert', 'created_by'
    ).all()
    filterset_fields = ['status', 'priority', 'assigned_to']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [require_permission('coordinators:read')()]
        return [require_permission('coordinators:write')()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if is_admin_or_superuser(user):
            return qs
        return qs.filter(assigned_to=user)

    def perform_create(self, serializer):
        obj = serializer.save()
        log_audit('create', 'coordinator_task', obj.pk, request=self.request)

    def perform_update(self, serializer):
        obj = serializer.save()
        if obj.status == 'completed' and not obj.completed_at:
            obj.completed_at = timezone.now()
            obj.save(update_fields=['completed_at'])
        log_audit('update', 'coordinator_task', obj.pk, request=self.request)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'completed_at'])
        log_audit('complete', 'coordinator_task', task.pk, request=request)
        return Response(CoordinatorTaskSerializer(task).data)


class CoordinationDashboardView(generics.GenericAPIView):
    permission_classes = [require_permission('coordinators:read')]

    def get(self, request):
        alerts_by_status = dict(
            Alert.objects.values_list('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        alerts_by_type = dict(
            Alert.objects.values_list('alert_type').annotate(count=Count('id')).values_list('alert_type', 'count')
        )
        pending_tasks = CoordinatorTask.objects.exclude(status='completed').count()
        upcoming_followups = Intervention.objects.filter(
            followup_date__gte=timezone.now().date(),
            followup_date__lte=timezone.now().date() + timezone.timedelta(days=7),
            status='pending',
        ).count()
        upcoming_communications = ParentCommunication.objects.filter(
            followup_date__gte=timezone.now().date(),
            followup_date__lte=timezone.now().date() + timezone.timedelta(days=7),
        ).count()
        pending_reports = TeacherWeeklyReport.objects.filter(status='draft').count()
        recent_tests = ClassTest.objects.select_related(
            'school_class', 'subject'
        ).order_by('-test_date')[:5]
        recent_tests_data = []
        for test in recent_tests:
            marks = list(test.marks.values_list('marks_obtained', flat=True))
            recent_tests_data.append({
                'id': str(test.id),
                'testName': test.test_name,
                'testDate': str(test.test_date),
                'className': test.school_class.name,
                'subjectName': test.subject.name,
                'term': test.term,
                'totalMarks': test.total_marks,
                'averageMarks': round(sum(marks) / len(marks), 1) if marks else 0,
                'studentCount': len(marks),
            })
        return Response({
            'alertsByStatus': {
                'open': alerts_by_status.get('open', 0),
                'pending': alerts_by_status.get('pending', 0),
                'resolved': alerts_by_status.get('resolved', 0),
            },
            'alertsByType': {
                'attendance': alerts_by_type.get('attendance', 0),
                'academic': alerts_by_type.get('academic', 0),
                'behavior': alerts_by_type.get('behavior', 0),
                'parent': alerts_by_type.get('parent', 0),
            },
            'pendingTasks': pending_tasks,
            'upcomingFollowups': upcoming_followups + upcoming_communications,
            'pendingReports': pending_reports,
            'recentTests': recent_tests_data,
        })
