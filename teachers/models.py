import uuid
from django.db import models


class Teacher(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designation = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    contact = models.CharField(max_length=255, blank=True, null=True)
    photo_path = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['designation']),
            models.Index(fields=['deleted_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.designation})"
