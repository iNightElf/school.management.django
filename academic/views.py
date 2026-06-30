from datetime import date, timedelta
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import (
    has_permission, require_permission, is_admin_or_superuser,
    is_class_teacher_of,
)
from core.models import SchoolSetting
from .models import RoutineTemplate, LessonPlan, Homework, Diary, ExamRoutine
from .serializers import (
    RoutineTemplateSerializer, LessonPlanSerializer,
    HomeworkSerializer, DiarySerializer, ExamRoutineSerializer,
    PeriodSettingSerializer,
)


def get_teacher_profile(user):
    return getattr(user, 'teacher_profile', None)


def get_teacher_assigned_class_ids(teacher):
    from teachers.models import TeacherSubject, ClassTeacher
    subject_classes = TeacherSubject.objects.filter(teacher=teacher).values_list('school_class_id', flat=True)
    ct_classes = ClassTeacher.objects.filter(teacher=teacher).values_list('school_class_id', flat=True)
    return set(list(subject_classes) + list(ct_classes))


# ─── Period Settings ────────────────────────────────────────────────

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def period_settings(request):
    if request.method == 'PUT':
        if not is_admin_or_superuser(request.user):
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

    setting, _ = SchoolSetting.objects.get_or_create(
        key='period_times',
        defaults={'value': '[]'},
    )

    if request.method == 'PUT':
        serializer = PeriodSettingSerializer(data=request.data, many=True)
        if serializer.is_valid():
            setting.value = serializer.data
            setting.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    import json
    try:
        data = json.loads(setting.value) if setting.value else []
    except (json.JSONDecodeError, TypeError):
        data = []
    return Response(data)


# ─── Admin ViewSets ────────────────────────────────────────────────

class AdminRoutineTemplateViewSet(viewsets.ModelViewSet):
    queryset = RoutineTemplate.objects.select_related('school_class', 'subject', 'teacher').all()
    serializer_class = RoutineTemplateSerializer
    filterset_fields = ['school_class', 'day', 'teacher']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [require_permission('academic:read')()]
        return [require_permission('academic:admin')()]


class AdminExamRoutineViewSet(viewsets.ModelViewSet):
    queryset = ExamRoutine.objects.select_related('school_class', 'subject').all()
    serializer_class = ExamRoutineSerializer
    filterset_fields = ['school_class', 'exam_name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [require_permission('academic:read')()]
        return [require_permission('academic:admin')()]


# ─── Teacher APIs ───────────────────────────────────────────────────

class TeacherRoutineViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def week(self, request):
        teacher = get_teacher_profile(request.user)
        if not teacher and not is_admin_or_superuser(request.user):
            return Response({'error': 'Teacher profile required'}, status=403)

        week_str = request.query_params.get('week')
        if week_str:
            wk_start = date.fromisoformat(week_str)
        else:
            today = date.today()
            wk_start = today - timedelta(days=today.weekday())

        wk_end = wk_start + timedelta(days=6)

        qs = RoutineTemplate.objects.select_related('school_class', 'subject', 'teacher').all()
        if not is_admin_or_superuser(request.user):
            class_ids = get_teacher_assigned_class_ids(teacher)
            qs = qs.filter(school_class_id__in=class_ids)

        routines = list(qs.order_by('day', 'period_number'))
        lesson_plans = LessonPlan.objects.filter(
            routine_template__in=[r.id for r in routines],
            week_start=wk_start,
        ).select_related('routine_template')
        lp_map = {lp.routine_template_id: lp for lp in lesson_plans}

        result = []
        for r in routines:
            item = RoutineTemplateSerializer(r).data
            lp = lp_map.get(r.id)
            item['lesson_plan'] = LessonPlanSerializer(lp).data if lp else None
            result.append(item)

        return Response({'week_start': str(wk_start), 'week_end': str(wk_end), 'periods': result})

    @action(detail=False, methods=['post'])
    def lesson_plan(self, request):
        teacher = get_teacher_profile(request.user)
        if not teacher and not is_admin_or_superuser(request.user):
            return Response({'error': 'Teacher profile required'}, status=403)

        routine_id = request.data.get('routine_template')
        week_start_str = request.data.get('week_start')

        if not routine_id or not week_start_str:
            return Response({'error': 'routine_template and week_start required'}, status=400)

        routine = RoutineTemplate.objects.filter(id=routine_id).first()
        if not routine:
            return Response({'error': 'Routine not found'}, status=404)

        if not is_admin_or_superuser(request.user):
            if routine.teacher != teacher:
                return Response({'error': 'Not your class'}, status=403)

        week_start = date.fromisoformat(week_start_str)
        lp, created = LessonPlan.objects.update_or_create(
            routine_template=routine,
            week_start=week_start,
            defaults={
                'topic': request.data.get('topic', ''),
                'learning_objectives': request.data.get('learning_objectives', ''),
                'activities': request.data.get('activities', ''),
                'materials': request.data.get('materials', ''),
                'assessment': request.data.get('assessment', ''),
                'remarks': request.data.get('remarks', ''),
                'completed': request.data.get('completed', False),
            },
        )
        return Response(LessonPlanSerializer(lp).data, status=status.HTTP_201_CREATED if created else 200)


class TeacherHomeworkViewSet(viewsets.ModelViewSet):
    serializer_class = HomeworkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        teacher = get_teacher_profile(self.request.user)
        if is_admin_or_superuser(self.request.user):
            qs = Homework.objects.select_related('school_class', 'subject', 'teacher').all()
        elif teacher:
            qs = Homework.objects.filter(teacher=teacher)
        else:
            return Homework.objects.none()

        class_id = self.request.query_params.get('class_id')
        subject_id = self.request.query_params.get('subject_id')
        published = self.request.query_params.get('published')
        if class_id:
            qs = qs.filter(school_class_id=class_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if published is not None:
            qs = qs.filter(published=published.lower() == 'true')
        return qs.select_related('school_class', 'subject', 'teacher').order_by('-date', '-created_at')

    def perform_create(self, serializer):
        teacher = get_teacher_profile(self.request.user)
        if teacher:
            serializer.save(teacher=teacher)
        else:
            serializer.save()


class TeacherDiaryViewSet(viewsets.ModelViewSet):
    serializer_class = DiarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        teacher = get_teacher_profile(self.request.user)
        if is_admin_or_superuser(self.request.user):
            qs = Diary.objects.select_related('school_class', 'subject', 'teacher').all()
        elif teacher:
            qs = Diary.objects.filter(teacher=teacher)
        else:
            return Diary.objects.none()

        class_id = self.request.query_params.get('class_id')
        subject_id = self.request.query_params.get('subject_id')
        if class_id:
            qs = qs.filter(school_class_id=class_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        return qs.select_related('school_class', 'subject', 'teacher').order_by('-date', '-created_at')

    def perform_create(self, serializer):
        teacher = get_teacher_profile(self.request.user)
        if teacher:
            serializer.save(teacher=teacher)
        else:
            serializer.save()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_dashboard(request):
    teacher = get_teacher_profile(request.user)
    if not teacher and not is_admin_or_superuser(request.user):
        return Response({'error': 'Teacher profile required'}, status=403)

    today = date.today()
    wk_start = today - timedelta(days=today.weekday())
    wk_end = wk_start + timedelta(days=6)

    if is_admin_or_superuser(request.user):
        class_ids = None
    else:
        class_ids = get_teacher_assigned_class_ids(teacher)

    qs = RoutineTemplate.objects.filter(day__in=['sunday', 'monday', 'tuesday', 'wednesday', 'thursday'])
    if class_ids is not None:
        qs = qs.filter(school_class_id__in=class_ids)
    today_routines = qs.filter(day=today.strftime('%A').lower()).select_related('school_class', 'subject')
    today_schedule = [
        {'period': r.period_number, 'subject': r.subject.name, 'class': r.school_class.name}
        for r in today_routines
    ]

    if class_ids is not None:
        pending_attendance = 0
    else:
        pending_attendance = 0

    if class_ids is not None:
        pending_lp = LessonPlan.objects.filter(
            routine_template__teacher=teacher,
            week_start=wk_start,
            completed=False,
        ).count()
    else:
        pending_lp = 0

    return Response({
        'today_schedule': today_schedule,
        'pending_attendance': pending_attendance,
        'pending_lesson_plans': pending_lp,
        'week_start': str(wk_start),
        'week_end': str(wk_end),
    })


# ─── Parent APIs ────────────────────────────────────────────────────

def get_parent_student_class_ids(user):
    from parents.models import ParentStudentLink
    return ParentStudentLink.objects.filter(
        parent=user,
    ).values_list('student__school_class_id', flat=True).distinct()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def parent_routine(request):
    class_ids = get_parent_student_class_ids(request.user)
    if not class_ids:
        return Response([])

    routines = RoutineTemplate.objects.filter(
        school_class_id__in=class_ids,
    ).select_related('school_class', 'subject', 'teacher').order_by('day', 'period_number')

    return Response(RoutineTemplateSerializer(routines, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def parent_homework(request):
    class_ids = get_parent_student_class_ids(request.user)
    if not class_ids:
        return Response([])

    homeworks = Homework.objects.filter(
        school_class_id__in=class_ids,
        published=True,
    ).select_related('school_class', 'subject', 'teacher').order_by('-date', '-created_at')

    return Response(HomeworkSerializer(homeworks, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def parent_diary(request):
    class_ids = get_parent_student_class_ids(request.user)
    if not class_ids:
        return Response([])

    diaries = Diary.objects.filter(
        school_class_id__in=class_ids,
    ).select_related('school_class', 'subject', 'teacher').order_by('-date', '-created_at')

    return Response(DiarySerializer(diaries, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def parent_exam_routine(request):
    class_ids = get_parent_student_class_ids(request.user)
    if not class_ids:
        return Response([])

    exams = ExamRoutine.objects.filter(
        school_class_id__in=class_ids,
    ).select_related('school_class', 'subject').order_by('date', 'start_time')

    return Response(ExamRoutineSerializer(exams, many=True).data)
