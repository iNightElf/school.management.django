from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction

from finance.models import FeeSchedule, FeeWaiver, StudentFeeAssignment
from students.models import Student
from finance.serializers import (
    FeeScheduleSerializer, FeeScheduleCopySerializer,
    FeeWaiverSerializer, StudentFeeAssignmentSerializer,
    StudentFeeAssignmentToggleSerializer, BulkAssignSerializer
)
from accounts.permissions import require_permission
from .base import PeriodClosedMixin, _param

class FeeScheduleViewSet(PeriodClosedMixin, viewsets.ModelViewSet):
    queryset = FeeSchedule.objects.select_related('academic_year', 'school_class').all()
    serializer_class = FeeScheduleSerializer
    filterset_fields = ['academic_year_id', 'school_class_id', 'category']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [require_permission('finance:read')()]
        return [require_permission('finance:write')()]

    @action(detail=False, methods=['post'])
    def copy_from_year(self, request):
        serializer = FeeScheduleCopySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with db_transaction.atomic():
            from_year_id = serializer.validated_data['from_academic_year_id']
            to_year_id = serializer.validated_data['to_academic_year_id']
            schedules = FeeSchedule.objects.filter(
                academic_year_id=from_year_id
            ).select_related('school_class')
            count = 0
            for s in schedules:
                _, created = FeeSchedule.objects.get_or_create(
                    academic_year_id=to_year_id,
                    school_class=s.school_class,
                    category=s.category,
                    frequency=s.frequency,
                    defaults={
                        'amount': s.amount,
                        'applicability': s.applicability,
                    }
                )
                if created:
                    count += 1
        return Response({'copied': count})


class FeeWaiverViewSet(PeriodClosedMixin, viewsets.ModelViewSet):
    queryset = FeeWaiver.objects.select_related('student', 'fee_schedule').all()
    serializer_class = FeeWaiverSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        student_id = _param(self.request, 'student_id', 'studentId')
        fee_schedule_id = _param(self.request, 'fee_schedule_id', 'feeScheduleId')
        active = _param(self.request, 'active')
        if student_id:
            qs = qs.filter(student_id=student_id)
        if fee_schedule_id:
            qs = qs.filter(fee_schedule_id=fee_schedule_id)
        if active is not None:
            qs = qs.filter(active=(active.lower() == 'true'))
        return qs

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [require_permission('finance:read')()]
        return [require_permission('finance:write')()]

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        waiver = self.get_object()
        waiver.active = False
        waiver.save(update_fields=['active'])
        return Response(FeeWaiverSerializer(waiver).data)


class StudentFeeAssignmentViewSet(PeriodClosedMixin, viewsets.ModelViewSet):
    queryset = StudentFeeAssignment.objects.select_related('student', 'fee_schedule').all()
    serializer_class = StudentFeeAssignmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        student_id = _param(self.request, 'student_id', 'studentId')
        fee_schedule_id = _param(self.request, 'fee_schedule_id', 'feeScheduleId')
        active = _param(self.request, 'active')
        if student_id:
            qs = qs.filter(student_id=student_id)
        if fee_schedule_id:
            qs = qs.filter(fee_schedule_id=fee_schedule_id)
        if active is not None:
            qs = qs.filter(active=(active.lower() == 'true'))
        return qs

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [require_permission('finance:read')()]
        return [require_permission('finance:write')()]

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        serializer = StudentFeeAssignmentToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        print(f"[DEBUG] Toggling assignment for student: {data['student_id']}, fee: {data['fee_schedule_id']}, active: {data['active']}")
        
        assignment, created = StudentFeeAssignment.objects.select_related(
            'student', 'fee_schedule'
        ).get_or_create(
            student_id=data['student_id'],
            fee_schedule_id=data['fee_schedule_id'],
            defaults={'active': data['active']},
        )
        print(f"[DEBUG] Assignment fetched/created: {assignment.id}, created: {created}, previous active: {assignment.active}")
        
        if created:
            # If newly created, ensure it matches requested active status (if False, explicitly set)
            if assignment.active != data['active']:
                assignment.active = data['active']
                assignment.save(update_fields=['active'])
                print(f"[DEBUG] New assignment updated to active: {assignment.active}")
        else:
            assignment.active = data['active']
            assignment.save(update_fields=['active'])
            print(f"[DEBUG] Existing assignment updated to active: {assignment.active}")
            
        return Response(StudentFeeAssignmentSerializer(assignment).data)

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        serializer = BulkAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        students = Student.objects.filter(
            school_class_id=data['class_id'],
            deleted_at__isnull=True
        )
        with db_transaction.atomic():
            existing = set(
                StudentFeeAssignment.objects.filter(
                    student__in=students,
                    fee_schedule_id=data['fee_schedule_id'],
                ).values_list('student_id', flat=True)
            )
            new_assignments = [
                StudentFeeAssignment(
                    student=s, 
                    fee_schedule_id=data['fee_schedule_id'],
                    starts_at=data.get('startsAt'),
                    ends_at=data.get('endsAt')
                )
                for s in students if s.id not in existing
            ]
            StudentFeeAssignment.objects.bulk_create(new_assignments)
            count = len(new_assignments)
        return Response({'assigned': count})
