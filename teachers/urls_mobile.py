from django.urls import path
from . import views_mobile

urlpatterns = [
    path('auth/pin/', views_mobile.pin_login, name='mobile-pin-login'),
    path('auth/set-pin/', views_mobile.set_pin, name='mobile-set-pin'),
    path('teachers/', views_mobile.mobile_teachers, name='mobile-teachers'),
    path('students/', views_mobile.mobile_students, name='mobile-students'),
    path('attendance/', views_mobile.mobile_get_attendance, name='mobile-get-attendance'),
    path('attendance/batch/', views_mobile.mobile_batch_attendance, name='mobile-batch-attendance'),
    path('attendance/class-report/', views_mobile.mobile_class_report, name='mobile-class-report'),
]
