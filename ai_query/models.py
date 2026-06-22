import uuid
from django.db import models
from django.conf import settings


class AIQueryLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    query = models.TextField()
    function_called = models.CharField(max_length=100, blank=True)
    arguments = models.JSONField(default=dict, blank=True)
    confidence = models.FloatField(default=0.0)
    execution_time_ms = models.IntegerField(default=0)
    result_count = models.IntegerField(default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['function_called']),
            models.Index(fields=['confidence']),
        ]
