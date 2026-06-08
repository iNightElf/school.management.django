import secrets
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .serializers import UserSerializer, UserRoleSerializer, RegisterSerializer
from .permissions import require_permission
from .models import EmailVerification

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.email_verified:
            raise AuthenticationFailed('Email not verified. Please verify your email before logging in.')
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        from django.db import transaction as db_transaction
        with db_transaction.atomic():
            is_first = not User.objects.select_for_update().exists()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if is_first:
            user.role = 'admin'
            user.email_verified = True
            user.save(update_fields=['role', 'email_verified'])
        else:
            self._send_verification(user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def _send_verification(self, user):
        token = secrets.token_urlsafe(32)
        EmailVerification.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        verify_url = f'{settings.FRONTEND_URL}/verify-email?token={token}'
        try:
            send_mail(
                subject='Verify your email - AL RAWA English School',
                message=f'Click the link to verify your email:\n\n{verify_url}\n\nThis link expires in 24 hours.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f'Failed to send verification email to {user.email}: {e}')


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class GetAllUsersView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [require_permission('users:read')]


class UpdateUserRoleView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [require_permission('users:write')]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance.role = serializer.validated_data['role']
        instance.save(update_fields=['role'])
        return Response(UserSerializer(instance).data)


class DeleteUserView(generics.DestroyAPIView):
    queryset = User.objects.all()
    permission_classes = [require_permission('users:write')]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance == request.user:
            return Response(
                {'error': 'Cannot delete yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuthGetSessionView(APIView):
    permission_classes = []

    def get(self, request):
        try:
            auth_result = JWTAuthentication().authenticate(request)
            if auth_result:
                user, _ = auth_result
                return JsonResponse({'user': {
                    'id': str(user.id),
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                    'image': user.image,
                    'emailVerified': user.email_verified,
                }})
        except AuthenticationFailed:
            pass
        return JsonResponse({'user': None})


class RoleChoicesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .models import User
        return Response([
            {'value': code, 'label': label}
            for code, label in User.ROLE_CHOICES
        ])


class SendVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.email_verified:
            return Response({'detail': 'Email already verified.'}, status=400)

        EmailVerification.objects.filter(user=user, used=False).update(used=True)

        token = secrets.token_urlsafe(32)
        EmailVerification.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24),
        )

        verify_url = f'{settings.FRONTEND_URL}/verify-email?token={token}'
        try:
            send_mail(
                subject='Verify your email - AL RAWA English School',
                message=f'Click the link to verify your email:\n\n{verify_url}\n\nThis link expires in 24 hours.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error('Failed to send verification email to %s: %s', user.email, e)
            return Response({'detail': 'Failed to send verification email. Please try again later.'}, status=500)

        return Response({'detail': 'Verification email sent.'})


class VerifyEmailView(APIView):
    permission_classes = []

    def get(self, request):
        token = request.query_params.get('token', '')
        if not token:
            return Response({'error': 'Token required.'}, status=400)

        try:
            verification = EmailVerification.objects.get(token=token)
        except EmailVerification.DoesNotExist:
            return Response({'error': 'Invalid token.'}, status=400)

        if not verification.is_valid():
            return Response({'error': 'Token expired or already used.'}, status=400)

        verification.used = True
        verification.save(update_fields=['used'])

        verification.user.email_verified = True
        verification.user.save(update_fields=['email_verified'])

        return Response({'detail': 'Email verified successfully.'})
