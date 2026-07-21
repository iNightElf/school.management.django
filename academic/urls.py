from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'academic'

router = DefaultRouter()
router.register(r'academic/routine-templates', views.AdminRoutineTemplateViewSet, basename='admin-routine')
router.register(r'academic/exam-routines', views.AdminExamRoutineViewSet, basename='admin-exam')
router.register(r'academic/suggestions', views.AdminSuggestionViewSet, basename='admin-suggestion')
router.register(r'teacher/routine', views.TeacherRoutineViewSet, basename='teacher-routine')
router.register(r'teacher/homework', views.TeacherHomeworkViewSet, basename='teacher-homework')
router.register(r'teacher/diary', views.TeacherDiaryViewSet, basename='teacher-diary')
router.register(r'teacher/leave-reasons', views.TeacherLeaveReasonViewSet, basename='teacher-leave-reason')
router.register(r'parents/suggestions', views.ParentSuggestionViewSet, basename='parent-suggestion')
router.register(r'parents/leave-reasons', views.ParentLeaveReasonViewSet, basename='parent-leave-reason')

urlpatterns = [
    path('', include(router.urls)),
    path('academic/period-settings/', views.period_settings, name='period-settings'),
    path('academic/exam-routine-notes/', views.exam_routine_notes, name='exam-routine-notes'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher-dashboard'),
    path('parents/routine/', views.parent_routine, name='parent-routine'),
    path('parents/homework/', views.parent_homework, name='parent-homework'),
    path('parents/diary/', views.parent_diary, name='parent-diary'),
    path('parents/exam-routine/', views.parent_exam_routine, name='parent-exam-routine'),
]
