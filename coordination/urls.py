from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'alerts', views.AlertViewSet, basename='alert')
router.register(r'interventions', views.InterventionViewSet, basename='intervention')
router.register(r'parent-communications', views.ParentCommunicationViewSet, basename='parent-communication')
router.register(r'weekly-reports', views.TeacherWeeklyReportViewSet, basename='weekly-report')
router.register(r'class-tests', views.ClassTestViewSet, basename='class-test')
router.register(r'class-test-marks', views.ClassTestMarkViewSet, basename='class-test-mark')
router.register(r'coordinator-tasks', views.CoordinatorTaskViewSet, basename='coordinator-task')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.CoordinationDashboardView.as_view(), name='coordination-dashboard'),
]
