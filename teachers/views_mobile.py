import logging

from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction as db_transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import Teacher, ClassTeacher
from students.models import Student
from core.models import SchoolClass, SchoolSetting
from attendance.models import AttendanceRecord, Holiday
from core.audit import log_audit

logger = logging.getLogger(__name__)
WEEKEND_DAYS_DEFAULT = '4,5'


from datetime import timedelta

class PinAccessToken(AccessToken):
    lifetime = timedelta(hours=24)


def _make_pin_token(teacher):
    token = PinAccessToken()
    token['teacher_id'] = str(teacher.id)
    token['teacher_name'] = teacher.name
    token['pin_auth'] = True
    return str(token)


def _get_pin_teacher(request):
    """Validate PIN bearer token and return the Teacher, or None."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    raw = auth.split(' ', 1)[1]
    if not raw:
        return None
    try:
        validated = AccessToken(raw)
        if not validated.get('pin_auth'):
            return None
        teacher_id = validated.get('teacher_id')
        if not teacher_id:
            return None
        return Teacher.objects.get(id=teacher_id, deleted_at__isnull=True)
    except (TokenError, Teacher.DoesNotExist, Exception):
        return None


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


@api_view(['POST'])
@permission_classes([AllowAny])
def pin_login(request):
    teacher_id = request.data.get('teacher_id')
    pin = request.data.get('pin')

    if not teacher_id or not pin:
        return Response({'error': 'teacher_id and pin are required'}, status=400)

    if not pin.isdigit() or len(pin) != 6:
        return Response({'error': 'PIN must be exactly 6 digits'}, status=400)

    try:
        teacher = Teacher.objects.get(id=teacher_id, deleted_at__isnull=True)
    except Teacher.DoesNotExist:
        return Response({'error': 'Teacher not found'}, status=404)

    if not teacher.pin:
        return Response({'error': 'No PIN set for this teacher'}, status=400)

    if not check_password(pin, teacher.pin):
        return Response({'error': 'Invalid PIN'}, status=403)

    token = _make_pin_token(teacher)

    classes = ClassTeacher.objects.filter(
        teacher=teacher,
    ).select_related('school_class').values(
        'school_class__id', 'school_class__name', 'school_class__order',
    ).order_by('school_class__order', 'school_class__name')

    return Response({
        'token': token,
        'teacher': {
            'id': str(teacher.id),
            'name': teacher.name,
            'designation': teacher.designation,
        },
        'classes': [
            {'id': str(c['school_class__id']), 'name': c['school_class__name']}
            for c in classes
        ],
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def set_pin(request):
    admin_user = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False)
    if not request.user.is_authenticated or not admin_user:
        return Response({'error': 'Admin access required'}, status=403)

    teacher_id = request.data.get('teacher_id')
    pin = request.data.get('pin')

    if not teacher_id or not pin:
        return Response({'error': 'teacher_id and pin are required'}, status=400)

    if not pin.isdigit() or len(pin) != 6:
        return Response({'error': 'PIN must be exactly 6 digits'}, status=400)

    try:
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        return Response({'error': 'Teacher not found'}, status=404)

    teacher.pin = make_password(pin)
    teacher.save(update_fields=['pin'])

    return Response({'status': 'ok'})


@api_view(['GET'])
@permission_classes([AllowAny])
def mobile_teachers(request):
    teachers = Teacher.objects.filter(
        deleted_at__isnull=True,
    ).exclude(pin='').values('id', 'name', 'designation').order_by('name')

    return Response({
        'teachers': [
            {'id': str(t['id']), 'name': t['name'], 'designation': t['designation']}
            for t in teachers
        ],
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def mobile_students(request):
    teacher = _get_pin_teacher(request)
    if not teacher:
        return Response({'error': 'Authentication required'}, status=401)

    class_id = request.query_params.get('class_id')
    if not class_id:
        return Response({'error': 'class_id query param is required'}, status=400)

    if not ClassTeacher.objects.filter(teacher=teacher, school_class_id=class_id).exists():
        return Response({'error': 'You are not assigned to this class'}, status=403)

    try:
        school_class = SchoolClass.objects.get(id=class_id)
    except SchoolClass.DoesNotExist:
        return Response({'error': 'Class not found'}, status=404)

    students = Student.objects.filter(
        school_class=school_class,
        deleted_at__isnull=True,
    ).order_by('roll', 'name').values('id', 'name', 'roll', 'photo_path')

    return Response({
        'class': {'id': str(school_class.id), 'name': school_class.name},
        'students': list(students),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def mobile_get_attendance(request):
    """Get existing attendance records for a class+date (PIN auth)."""
    teacher = _get_pin_teacher(request)
    if not teacher:
        return Response({'error': 'Authentication required'}, status=401)

    class_id = request.query_params.get('class_id')
    date_param = request.query_params.get('date')
    if not class_id or not date_param:
        return Response({'error': 'class_id and date are required'}, status=400)

    records = AttendanceRecord.objects.filter(
        school_class_id=class_id, date=date_param,
    ).values('student', 'status', 'term', 'session')

    return Response(list(records))


@api_view(['POST'])
@permission_classes([AllowAny])
def mobile_batch_attendance(request):
    """Batch create/update attendance records (PIN auth)."""
    teacher = _get_pin_teacher(request)
    if not teacher:
        return Response({'error': 'Authentication required'}, status=401)

    class_id = request.data.get('school_class')
    date_str = request.data.get('date')
    term = request.data.get('term')
    session_data = request.data.get('session')
    records = request.data.get('records')

    if not class_id or not date_str or not records:
        return Response({'error': 'school_class, date, and records are required'}, status=400)

    from datetime import datetime
    try:
        att_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return Response({'error': 'Invalid date format (YYYY-MM-DD)'}, status=400)

    if not isinstance(records, dict) or len(records) == 0:
        return Response({'error': 'records must be a non-empty object'}, status=400)

    try:
        school_class = SchoolClass.objects.get(id=class_id)
    except SchoolClass.DoesNotExist:
        return Response({'error': 'School class not found'}, status=404)

    if not ClassTeacher.objects.filter(teacher=teacher, school_class=school_class).exists():
        return Response({'error': 'You are not assigned to this class'}, status=403)

    # Validate students
    student_ids = list(records.keys())
    existing = Student.objects.filter(id__in=student_ids, school_class_id=class_id)
    if existing.count() != len(student_ids):
        return Response({'error': 'One or more students not found in this class'}, status=400)

    # Validate date is not weekend
    weekend_set = _get_weekend_set()
    if att_date.weekday() in weekend_set:
        return Response({'error': 'Cannot mark attendance on a weekend day'}, status=400)

    # Validate date is not holiday
    holiday_set = _get_holiday_dates(year=att_date.year)
    if att_date in holiday_set:
        return Response({'error': 'Cannot mark attendance on a holiday'}, status=400)

    with db_transaction.atomic():
        for student_id, status_val in records.items():
            AttendanceRecord.objects.update_or_create(
                student_id=student_id, date=att_date,
                defaults={
                    'school_class': school_class,
                    'term': term or '',
                    'session': session_data or '',
                    'status': status_val,
                    'marked_by': None,
                },
            )

    log_audit('batch_attendance', 'attendance',
              details={'class_id': str(class_id), 'date': str(att_date),
                       'term': term, 'session': session_data, 'count': len(records),
                       'via': 'pin_auth', 'teacher': teacher.name},
              request=request)

    return Response({'status': 'ok', 'count': len(records)})


@api_view(['GET'])
@permission_classes([AllowAny])
def mobile_class_report(request):
    """Class attendance report for a date range (PIN auth)."""
    try:
        return _mobile_class_report_logic(request)
    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.exception('mobile_class_report failed')
        return Response({'error': 'Failed to load report'}, status=500)


def _mobile_class_report_logic(request):
    teacher = _get_pin_teacher(request)
    if not teacher:
        return Response({'error': 'Authentication required'}, status=401)

    class_id = request.query_params.get('class_id')
    from_date = request.query_params.get('from')
    to_date = request.query_params.get('to')
    term = request.query_params.get('term')
    session_data = request.query_params.get('session')

    if not class_id or not from_date or not to_date:
        return Response({'error': 'class_id, from, and to are required'}, status=400)

    try:
        school_class = SchoolClass.objects.get(id=class_id)
    except SchoolClass.DoesNotExist:
        return Response({'error': 'Class not found'}, status=404)

    if not ClassTeacher.objects.filter(teacher=teacher, school_class=school_class).exists():
        return Response({'error': 'You are not assigned to this class'}, status=403)

    students_qs = list(
        Student.objects.filter(
            school_class=school_class, deleted_at__isnull=True,
        )
        .order_by('roll', 'name')
        .values('id', 'name', 'roll')
    )

    qs = AttendanceRecord.objects.filter(
        school_class=school_class, date__gte=from_date, date__lte=to_date,
    )
    if term:
        qs = qs.filter(term=term)
    if session_data:
        qs = qs.filter(session=session_data)

    try:
        records_list = list(qs.values('student_id', 'date', 'status'))
        dates = sorted(
            {r['date'] for r in records_list},
            key=lambda d: str(d),
        )
    except Exception:
        records_list = []
        dates = []

    student_ids = [str(s['id']) for s in students_qs]

    grid: dict[str, dict[str, str]] = {}
    student_summary: dict[str, dict[str, int]] = {}

    for rec in records_list:
        try:
            sid = str(rec['student_id'])
            d = rec['date'].isoformat()
            st = str(rec['status'])
        except Exception:
            continue

        grid.setdefault(sid, {})[d] = st
        ss = student_summary.setdefault(sid, {'present': 0, 'absent': 0, 'late': 0, 'excused': 0})
        if st in ss:
            ss[st] += 1

    for sid in student_ids:
        grid.setdefault(sid, {})
        student_summary.setdefault(sid, {'present': 0, 'absent': 0, 'late': 0, 'excused': 0})

    full_summary = {}
    for sid in student_ids:
        ss = student_summary[sid]
        total = ss['present'] + ss['absent'] + ss['late'] + ss['excused']
        pct = round(ss['present'] / total * 100, 1) if total > 0 else 0.0
        full_summary[sid] = {**ss, 'total': total, 'pct': pct}

    return Response({
        'class': {'id': str(school_class.id), 'name': school_class.name},
        'students': [{'id': str(s['id']), 'name': s['name'], 'roll': s['roll']} for s in students_qs],
        'dates': [d.isoformat() for d in dates],
        'grid': grid,
        'summary': full_summary,
    })
