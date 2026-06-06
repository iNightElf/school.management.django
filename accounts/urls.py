from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('auth/me/', views.MeView.as_view(), name='me'),
    path('auth/get-session/', views.AuthGetSessionView.as_view(), name='auth-get-session'),
    path('auth/send-verification/', views.SendVerificationView.as_view(), name='send-verification'),
    path('auth/verify-email/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('users/', views.GetAllUsersView.as_view(), name='users-list'),
    path('users/roles/', views.RoleChoicesView.as_view(), name='users-roles'),
    path('users/<uuid:pk>/role/', views.UpdateUserRoleView.as_view(), name='user-role'),
    path('users/<uuid:pk>/', views.DeleteUserView.as_view(), name='user-delete'),
]
