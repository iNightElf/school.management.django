import json
import logging
from .models import AuditLog

logger = logging.getLogger(__name__)


def log_audit(action, entity_type, entity_id=None, details=None, request=None):
    """Create an audit log entry.

    Args:
        action: e.g. 'create', 'update', 'delete', 'cancel', 'restore', 'graduate'
        entity_type: e.g. 'student', 'teacher', 'transaction', 'class'
        entity_id: UUID or string ID of the affected object
        details: dict or string with extra context
        request: Django HttpRequest — extracts user info
    """
    user_id = None
    user_name = None
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        user_id = str(request.user.id)
        user_name = getattr(request.user, 'name', None) or getattr(request.user, 'email', None)

    if isinstance(details, dict):
        details = json.dumps(details, default=str)

    try:
        AuditLog.objects.create(
            user_id=user_id,
            user_name=user_name,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            details=details,
        )
    except Exception as e:
        logger.warning(f"Audit log failed: {e}")


class AuditLogMixin:
    """Mixin for ModelViewSet — auto-logs create/update/delete.

    Sets self._audit_entity_type from the viewset.
    Override _audit_entity_type on the viewset, or it defaults to the model name.
    """

    _audit_entity_type = None

    def _get_entity_type(self):
        if self._audit_entity_type:
            return self._audit_entity_type
        if hasattr(self, 'queryset') and self.queryset is not None:
            return self.queryset.model._meta.model_name
        return 'unknown'

    def _entity_id_from_obj(self, obj):
        if hasattr(obj, 'pk'):
            return str(obj.pk)
        return None

    def perform_create(self, serializer):
        obj = serializer.save()
        log_audit(
            action='create',
            entity_type=self._get_entity_type(),
            entity_id=self._entity_id_from_obj(obj),
            details={'data': serializer.validated_data} if hasattr(serializer, 'validated_data') else None,
            request=self.request,
        )
        return obj

    def perform_update(self, serializer):
        obj = serializer.save()
        log_audit(
            action='update',
            entity_type=self._get_entity_type(),
            entity_id=self._entity_id_from_obj(obj),
            request=self.request,
        )
        return obj

    def perform_destroy(self, instance):
        entity_type = self._get_entity_type()
        entity_id = self._entity_id_from_obj(instance)
        instance.delete()
        log_audit(
            action='delete',
            entity_type=entity_type,
            entity_id=entity_id,
            request=self.request,
        )
