from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Teacher
from .serializers import TeacherSerializer
from accounts.permissions import require_permission
from core.mixins import PhotoHandleMixin


class TeacherViewSet(PhotoHandleMixin, viewsets.ModelViewSet):
    serializer_class = TeacherSerializer
    photo_prefix = 'teachers'
    filterset_fields = ['designation']

    def get_permissions(self):
        if self.action == 'photo':
            from rest_framework.permissions import AllowAny
            return [AllowAny()]
        if self.action in ['list', 'retrieve']:
            return [require_permission('teachers:read')()]
        return [require_permission('teachers:write')()]

    def get_queryset(self):
        qs = Teacher.objects.all()
        show_deleted = self.request.query_params.get('deleted', 'false').lower() == 'true'
        if not show_deleted:
            qs = qs.filter(deleted_at__isnull=True)
        return qs

    @action(detail=False, methods=['post'])
    def import_teachers(self, request):
        return Response({'status': 'not_implemented', 'detail': 'Import from file not yet implemented'})
