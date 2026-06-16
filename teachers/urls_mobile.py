from django.urls import path
from . import views_mobile

urlpatterns = [
    path('auth/pin/', views_mobile.pin_login, name='mobile-pin-login'),
    path('auth/set-pin/', views_mobile.set_pin, name='mobile-set-pin'),
    path('students/', views_mobile.mobile_students, name='mobile-students'),
    path('teachers/', views_mobile.mobile_teachers, name='mobile-teachers'),
]
