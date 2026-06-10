from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'quiz', views.QuizViewSet, basename='quiz')
router.register(r'riddle', views.RiddleViewSet, basename='riddle')
router.register(r'tips', views.TipViewSet, basename='tips')
router.register(r'challenges', views.ChallengeViewSet, basename='challenges')
router.register(r'mood', views.MoodViewSet, basename='mood')
router.register(r'lesson-plans', views.LessonPlanViewSet, basename='lesson-plans')
router.register(r'streak', views.StreakViewSet, basename='streak')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/regenerate/', views.regenerate_content, name='regenerate-content'),
]
