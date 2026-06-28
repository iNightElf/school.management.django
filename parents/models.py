import uuid
from django.db import models
from django.conf import settings


class ParentStudentLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='parent_links',
        limit_choices_to={'role': 'parent'},
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='parent_links',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['parent', 'student'],
                name='unique_parent_student',
            ),
        ]
        verbose_name = 'parent-student link'
        verbose_name_plural = 'parent-student links'

    def __str__(self):
        return f"{self.parent.name} → {self.student.name}"


class PushSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='push_subscriptions',
    )
    endpoint = models.URLField(max_length=500)
    p256dh_key = models.CharField(max_length=256)
    auth_key = models.CharField(max_length=64)
    user_agent = models.CharField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'push subscription'
        verbose_name_plural = 'push subscriptions'
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Push sub for {self.user.email}"


class NotificationLog(models.Model):
    EVENT_TYPES = [
        ('attendance_marked', 'Attendance Marked'),
        ('fee_received', 'Fee Received'),
        ('result_published', 'Result Published'),
        ('announcement', 'Announcement'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notification_logs',
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default='')
    payload = models.JSONField(blank=True, default=dict)
    sent_at = models.DateTimeField(auto_now_add=True)
    error = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'notification log'
        verbose_name_plural = 'notification logs'
        indexes = [
            models.Index(fields=['user', '-sent_at']),
            models.Index(fields=['event_type']),
        ]

    def __str__(self):
        return f"[{self.event_type}] {self.title} → {self.user.email}"


class Announcement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='announcements',
    )
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'announcement'
        verbose_name_plural = 'announcements'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
