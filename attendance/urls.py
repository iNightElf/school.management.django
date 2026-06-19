from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'attendance', views.AttendanceViewSet, basename='attendance')
router.register(r'holidays', views.HolidayViewSet, basename='holiday')

urlpatterns = [
    path('', include(router.urls)),
    path('attendance/student/<uuid:student_id>/',
         views.AttendanceViewSet.as_view({'get': 'student_month'}),
         name='student-attendance-month'),
    path('attendance/class-daily-report/',
         views.AttendanceViewSet.as_view({'get': 'class_daily_report'}),
         name='class-daily-report'),
    path('attendance/all-classes-daily/',
         views.AttendanceViewSet.as_view({'get': 'all_classes_daily'}),
         name='all-classes-daily'),
    path('attendance/monthly-report/',
         views.AttendanceViewSet.as_view({'get': 'monthly_report'}),
         name='monthly-report'),
]
