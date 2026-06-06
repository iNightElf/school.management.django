import base64
import logging
from django.utils import timezone
from django.shortcuts import redirect
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework import status
from core.supabase_storage import upload_photo, delete_photo, get_signed_url

logger = logging.getLogger(__name__)


class PhotoHandleMixin:
    photo_prefix = ''

    def perform_create(self, serializer):
        instance = serializer.save()
        self._handle_photo(instance, self.request.data.get('photo'))

    def perform_update(self, serializer):
        instance = self.get_object()
        self._handle_photo(instance, self.request.data.get('photo'))
        serializer.save()

    def perform_destroy(self, instance):
        if instance.photo_path:
            delete_photo(instance.photo_path)
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])

    def _handle_photo(self, instance, photo_data):
        if not photo_data:
            if instance.photo_path:
                delete_photo(instance.photo_path)
                instance.photo_path = None
                instance.save(update_fields=['photo_path'])
            return
        if photo_data.startswith('http'):
            return
        path = f"{self.photo_prefix}/{instance.id}.jpg"
        try:
            raw = base64.b64decode(photo_data.split(',', 1)[-1] if ',' in photo_data else photo_data)
            ok = upload_photo(path, raw)
            if not ok:
                logger.error("Supabase upload returned false for %s/%s", self.photo_prefix, instance.id)
                return
            instance.photo_path = path
            instance.save(update_fields=['photo_path'])
        except (ValueError, OSError, Exception) as e:
            logger.error("Photo handle failed for %s/%s: %s", self.photo_prefix, instance.id, e)

    @action(detail=True, methods=['get'], permission_classes=[])
    def photo(self, request, pk=None):
        from django.core import signing
        token = request.query_params.get('token')
        authenticated = request.user and request.user.is_authenticated
        
        if not authenticated:
            if not token:
                return Response({'error': 'Authentication required'}, status=401)
            try:
                data = signing.loads(token, salt='photo-access', max_age=3600)
                if str(data.get('id')) != str(pk):
                    return Response({'error': 'Invalid token'}, status=403)
            except Exception:
                return Response({'error': 'Invalid or expired token'}, status=403)

        instance = self.get_object()
        if instance.photo_path:
            url = get_signed_url(instance.photo_path)
            if url:
                return redirect(url)
        return Response({'error': 'No photo'}, status=404)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        model_class = self.queryset.model if hasattr(self, 'queryset') else self.get_serializer().Meta.model
        try:
            instance = model_class.objects.get(pk=pk)
        except model_class.DoesNotExist:
            raise NotFound(f"{model_class.__name__} not found.")
        instance.deleted_at = None
        instance.save(update_fields=['deleted_at'])
        serializer_class = self.get_serializer_class()
        return Response(serializer_class(instance).data)
