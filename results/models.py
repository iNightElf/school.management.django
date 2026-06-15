import uuid
from django.db import models


class Result(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        'students.Student', on_delete=models.PROTECT,
        related_name='results'
    )
    session = models.CharField(max_length=255, default='')
    term = models.CharField(max_length=255)
    marks = models.JSONField(default=dict)
    attendance = models.JSONField(blank=True, null=True)
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Result'
        verbose_name_plural = 'Results'
        constraints = [
            models.UniqueConstraint(fields=['student', 'term', 'session'], name='unique_result_per_student_term_session'),
        ]
        indexes = [
            models.Index(fields=['session']),
            models.Index(fields=['student', 'session']),
            models.Index(fields=['session', 'term']),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.term} ({self.session})"
