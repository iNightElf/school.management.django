from rest_framework import viewsets
from .models import Book
from .serializers import BookSerializer
from accounts.permissions import require_permission
from core.audit import AuditLogMixin


class BookViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = Book.objects.select_related('school_class').all()
    serializer_class = BookSerializer
    filterset_fields = ['school_class_id']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [require_permission('books:read')()]
        return [require_permission('books:write')()]

    def get_queryset(self):
        qs = super().get_queryset()
        class_id = self.request.query_params.get('class_id')
        if class_id:
            qs = qs.filter(school_class_id=class_id)
        return qs
