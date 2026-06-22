from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Staff
from .serializers import StaffSerializer
from accounts.permissions import require_permission, require_photo_access
from core.mixins import PhotoHandleMixin
from core.audit import AuditLogMixin


class StaffViewSet(PhotoHandleMixin, AuditLogMixin, viewsets.ModelViewSet):
    serializer_class = StaffSerializer
    photo_prefix = 'staff'
    filterset_fields = ['role']

    def get_permissions(self):
        if self.action == 'photo':
            return [require_photo_access('staff:read')()]
        if self.action in ['list', 'retrieve']:
            return [require_permission('staff:read')()]
        return [require_permission('staff:write')()]

    def get_queryset(self):
        qs = Staff.objects.all()
        show_deleted = self.request.query_params.get('deleted', 'false').lower() == 'true'
        if not show_deleted:
            qs = qs.filter(deleted_at__isnull=True)
        return qs

    @action(detail=False, methods=['post'], url_path='import')
    def import_staff(self, request):
        staff_data = request.data.get('staff', [])
        if not staff_data:
            return Response({'error': 'No staff data provided'}, status=400)
        created = 0
        errors = []
        for i, row in enumerate(staff_data):
            try:
                Staff.objects.create(
                    name=row.get('name', '').strip(),
                    role=row.get('role', '').strip(),
                    email=row.get('email', '').strip(),
                    contact=row.get('contact', '').strip(),
                )
                created += 1
            except Exception as e:
                errors.append({'row': i + 1, 'error': str(e)})
        return Response({'created': created, 'errors': errors})
