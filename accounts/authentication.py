from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


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
