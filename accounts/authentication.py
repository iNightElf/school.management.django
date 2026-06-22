from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """JWT authentication that reads tokens from httponly cookies."""

    def authenticate(self, request):
        # Try Authorization header first (backward compat).
        # If it fails (e.g. PIN token without user_id), fall through quietly.
        try:
            header_result = super().authenticate(request)
            if header_result:
                return header_result
        except AuthenticationFailed:
            pass

        # Fall back to cookie
        raw_token = request.COOKIES.get(settings.SIMPLE_JWT.get('ACCESS_COOKIE', 'access_token'))
        if not raw_token:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except Exception:
            return None


class PinAuthentication(BaseAuthentication):
    """PIN JWT auth for mobile endpoints. Sets request.user to Teacher instance."""

    def authenticate(self, request):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return None
        raw = auth.split(' ', 1)[1]
        if not raw:
            return None
        try:
            validated = AccessToken(raw)
            if not validated.get('pin_auth'):
                return None
            teacher_id = validated.get('teacher_id')
            if not teacher_id:
                return None
            from teachers.models import Teacher
            teacher = Teacher.objects.get(id=teacher_id, deleted_at__isnull=True)
            teacher.is_authenticated = True  # ponytail: duck-punch for DRF compat
            return (teacher, validated)
        except (TokenError, Teacher.DoesNotExist):
            return None
