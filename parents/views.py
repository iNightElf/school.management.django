import calendar
import json
import logging
import os
from datetime import date
from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsParentOfStudent
from accounts.permissions import require_permission
from .serializers import (
    ParentStudentSerializer, ParentAttendanceSerializer,
    ParentFeeStatusSerializer, ParentResultSerializer,
)
from .models import PushSubscription, Announcement
from students.models import Student
from attendance.models import AttendanceRecord, Holiday
from results.models import Result
from finance.models import FeeSchedule, StudentFeeAssignment, Transaction
from core.models import SchoolSetting

logger = logging.getLogger(__name__)

WEEKEND_DAYS_DEFAULT = '4,5'


def _get_weekend_set():
    try:
        raw = SchoolSetting.objects.get(key='weekend_days').value
        return {int(x.strip()) for x in raw.split(',') if x.strip().isdigit()}
    except SchoolSetting.DoesNotExist:
        return {int(x) for x in WEEKEND_DAYS_DEFAULT.split(',')}


def _get_holiday_dates(year=None, month=None):
    qs = Holiday.objects.all()
    if year:
        qs = qs.filter(date__year=year)
    if month is not None:
        qs = qs.filter(date__month=month)
    return set(qs.values_list('date', flat=True))


class MyStudentsView(APIView):
    permission_classes = [IsParentOfStudent]

    def get(self, request):
        student_ids = request.user.parent_links.values_list('student_id', flat=True)
        students = Student.objects.filter(
            id__in=student_ids, deleted_at__isnull=True
        ).select_related('school_class').order_by('name')

        data = [{
            'id': s.id,
            'studentId': s.student_id,
            'name': s.name,
            'roll': s.roll,
            'klass': s.school_class.name if s.school_class else '',
            'session': s.session,
            'photoUrl': None,
        } for s in students]
        return Response(ParentStudentSerializer(data, many=True).data)


class StudentAttendanceView(APIView):
    permission_classes = [IsParentOfStudent]

    def get(self, request, student_id):
        parent_student_ids = set(
            request.user.parent_links.values_list('student_id', flat=True)
        )
        if student_id not in parent_student_ids:
            return Response({'error': 'Student not found'}, status=404)

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=404)

        year = request.query_params.get('year')
        month = request.query_params.get('month')
        today = timezone.now().date()
        year = int(year) if year else today.year
        month = int(month) if month else today.month

        records = AttendanceRecord.objects.filter(
            student_id=student_id,
            date__year=year,
            date__month=month,
        ).order_by('date')

        weekend_set = _get_weekend_set()
        known_holidays = _get_holiday_dates(year=year, month=month)

        class_date_records = AttendanceRecord.objects.filter(
            school_class=student.school_class,
            date__year=year,
            date__month=month,
        ).values('date').annotate(
            total=Count('student', distinct=True),
            absent_count=Count('id', filter=Q(status='absent')),
        )

        all_absent_dates = {
            row['date'] for row in class_date_records
            if row['total'] == row['absent_count']
        }

        records_by_date = {r.date: r.status for r in records}

        _, days_in_month = calendar.monthrange(year, month)
        days = []
        for day in range(1, days_in_month + 1):
            d = date(year, month, day)
            entry = {'date': d.isoformat(), 'weekday': d.weekday()}
            if d.weekday() in weekend_set:
                entry['type'] = 'weekend'
                entry['status'] = None
            elif d in known_holidays:
                entry['type'] = 'holiday'
                entry['status'] = None
            elif d in all_absent_dates:
                entry['type'] = 'de_facto_holiday'
                entry['status'] = None
            elif d in records_by_date:
                entry['type'] = 'marked'
                entry['status'] = records_by_date[d]
            else:
                entry['type'] = 'unmarked'
                entry['status'] = None
            days.append(entry)

        data = {
            'student': {'id': str(student.id), 'name': student.name, 'roll': student.roll},
            'year': year,
            'month': month,
            'days': days,
        }
        return Response(ParentAttendanceSerializer(data).data)


class StudentFeesView(APIView):
    permission_classes = [IsParentOfStudent]

    def get(self, request, student_id):
        parent_student_ids = set(
            request.user.parent_links.values_list('student_id', flat=True)
        )
        if student_id not in parent_student_ids:
            return Response({'error': 'Student not found'}, status=404)

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=404)

        assignments = StudentFeeAssignment.objects.filter(
            student_id=student_id, active=True
        ).select_related('fee_schedule')

        schedules = []
        total_due = Decimal('0.00')
        for a in assignments:
            fs = a.fee_schedule
            schedules.append({
                'category': fs.category,
                'amount': fs.amount,
                'frequency': fs.frequency,
                'assigned': True,
            })
            total_due += fs.amount

        paid_agg = Transaction.objects.filter(
            student_id=student_id,
            transaction_type='INCOME',
            is_cancelled=False,
        ).aggregate(total=Sum('amount'))
        total_paid = paid_agg['total'] or Decimal('0.00')

        data = {
            'totalDue': total_due,
            'totalPaid': total_paid,
            'balance': total_due - total_paid,
            'schedules': schedules,
        }
        return Response(ParentFeeStatusSerializer(data).data)


class StudentResultsView(APIView):
    permission_classes = [IsParentOfStudent]

    def get(self, request, student_id):
        parent_student_ids = set(
            request.user.parent_links.values_list('student_id', flat=True)
        )
        if student_id not in parent_student_ids:
            return Response({'error': 'Student not found'}, status=404)

        results = Result.objects.filter(student_id=student_id)
        session = request.query_params.get('session')
        term = request.query_params.get('term')
        if session:
            results = results.filter(session=session)
        if term:
            results = results.filter(term=term)
        results = results.order_by('-created_at')

        data = [{
            'id': r.id,
            'session': r.session,
            'term': r.term,
            'marks': r.marks,
            'comment': r.comment,
            'createdAt': r.created_at.isoformat(),
        } for r in results]
        return Response(ParentResultSerializer(data, many=True).data)


class PushSubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        endpoint = data.get('endpoint')
        p256dh = data.get('keys', {}).get('p256dh')
        auth = data.get('keys', {}).get('auth')
        if not endpoint or not p256dh or not auth:
            return Response({'error': 'Missing subscription data'}, status=400)

        sub, created = PushSubscription.objects.update_or_create(
            user=request.user,
            endpoint=endpoint,
            defaults={
                'p256dh_key': p256dh,
                'auth_key': auth,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            },
        )
        return Response({'status': 'subscribed'}, status=201 if created else 200)

    def delete(self, request):
        endpoint = request.data.get('endpoint')
        if endpoint:
            PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
        else:
            PushSubscription.objects.filter(user=request.user).delete()
        return Response({'status': 'unsubscribed'})


class VapidKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        val = os.environ.get('VAPID_PUBLIC_KEY', '')
        logger.info("VAPID_PUBLIC_KEY=%s", val)
        return Response({'publicKey': val})


class AnnouncementListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        announcements = Announcement.objects.all()[:20]
        data = [{
            'id': a.id,
            'title': a.title,
            'body': a.body,
            'author': a.author.name if a.author else 'Admin',
            'createdAt': a.created_at.isoformat(),
        } for a in announcements]
        return Response(data)

    def post(self, request):
        perm = require_permission('students:write')()
        if not perm.has_permission(request, self):
            return Response({'error': 'Permission denied'}, status=403)
        title = request.data.get('title')
        body = request.data.get('body', '')
        if not title:
            return Response({'error': 'Title required'}, status=400)
        announcement = Announcement.objects.create(
            author=request.user, title=title, body=body,
        )
        from .services import notify_all_parents
        notify_all_parents(title, body, url='/#/parent/announcements')
        return Response({
            'id': announcement.id,
            'title': announcement.title,
            'body': announcement.body,
            'createdAt': announcement.created_at.isoformat(),
        }, status=201)
