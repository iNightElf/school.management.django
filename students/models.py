import uuid
from django.db import models


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_class = models.ForeignKey(
        'core.SchoolClass', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='students'
    )
    student_id = models.CharField(max_length=20, unique=True)
    roll = models.CharField(max_length=255, blank=True, null=True)
    session = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    father_name = models.CharField(max_length=255, blank=True, null=True)
    mother_name = models.CharField(max_length=255, blank=True, null=True)
    contact = models.CharField(max_length=255, blank=True, null=True)
    photo_path = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    graduated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['session']),
            models.Index(fields=['school_class_id', 'deleted_at'], name='student_class_active_idx'),
            models.Index(fields=['deleted_at', 'session'], name='student_session_active_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.student_id})"
