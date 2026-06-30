from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'academic/routine-templates', views.AdminRoutineTemplateViewSet, basename='admin-routine')
router.register(r'academic/exam-routines', views.AdminExamRoutineViewSet, basename='admin-exam')
router.register(r'teacher/routine', views.TeacherRoutineViewSet, basename='teacher-routine')
router.register(r'teacher/homework', views.TeacherHomeworkViewSet, basename='teacher-homework')
router.register(r'teacher/diary', views.TeacherDiaryViewSet, basename='teacher-diary')

urlpatterns = [
    path('', include(router.urls)),
    path('academic/period-settings/', views.period_settings, name='period-settings'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher-dashboard'),
    path('parents/routine/', views.parent_routine, name='parent-routine'),
    path('parents/homework/', views.parent_homework, name='parent-homework'),
    path('parents/diary/', views.parent_diary, name='parent-diary'),
    path('parents/exam-routine/', views.parent_exam_routine, name='parent-exam-routine'),
]
