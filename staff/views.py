from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Staff
from .serializers import StaffSerializer
from accounts.permissions import require_permission
from core.mixins import PhotoHandleMixin


class StaffViewSet(PhotoHandleMixin, viewsets.ModelViewSet):
    serializer_class = StaffSerializer
    photo_prefix = 'staff'
    filterset_fields = ['role']

    def get_permissions(self):
        if self.action == 'photo':
            from rest_framework.permissions import AllowAny
            return [AllowAny()]
        if self.action in ['list', 'retrieve']:
            return [require_permission('staff:read')()]
        return [require_permission('staff:write')()]

    def get_queryset(self):
        qs = Staff.objects.all()
        show_deleted = self.request.query_params.get('deleted', 'false').lower() == 'true'
        if not show_deleted:
            qs = qs.filter(deleted_at__isnull=True)
        return qs

    @action(detail=False, methods=['post'])
    def import_staff(self, request):
        return Response({'status': 'not_implemented', 'detail': 'Import from file not yet implemented'})
