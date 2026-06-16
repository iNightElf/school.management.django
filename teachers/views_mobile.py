from django.contrib.auth.hashers import make_password, check_password
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from .models import Teacher, ClassTeacher
from students.models import Student
from core.models import SchoolClass


def _make_pin_token(teacher):
    token = AccessToken()
    token['teacher_id'] = str(teacher.id)
    token['teacher_name'] = teacher.name
    token['pin_auth'] = True
    return str(token)


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
@permission_classes([IsAuthenticated])
def mobile_students(request):
    class_id = request.query_params.get('class_id')
    if not class_id:
        return Response({'error': 'class_id query param is required'}, status=400)

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
