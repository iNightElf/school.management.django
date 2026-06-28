from django.urls import path
from django.conf import settings
from django.http import JsonResponse
from . import views

urlpatterns = [
    path('parents/my-students/', views.MyStudentsView.as_view(), name='parent-my-students'),
    path('parents/attendance/<uuid:student_id>/', views.StudentAttendanceView.as_view(), name='parent-student-attendance'),
    path('parents/fees/<uuid:student_id>/', views.StudentFeesView.as_view(), name='parent-student-fees'),
    path('parents/results/<uuid:student_id>/', views.StudentResultsView.as_view(), name='parent-student-results'),
    path('parents/push/subscribe/', views.PushSubscribeView.as_view(), name='push-subscribe'),
    path('parents/push/vapid-key/', lambda r: JsonResponse({'publicKey': settings.VAPID_PUBLIC_KEY}), name='vapid-key'),
    path('parents/announcements/', views.AnnouncementListView.as_view(), name='parent-announcements'),
]
