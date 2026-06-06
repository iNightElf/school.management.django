import uuid
from django.db import models
from django.db.models import Q


class SchoolClass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    full_marks = models.IntegerField()
    order = models.IntegerField(default=0)
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE,
        related_name='subjects'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'school_class'], name='unique_subject_per_class'),
        ]
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.school_class.name})"


class AcademicYear(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class SchoolSetting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()

    def __str__(self):
        return self.key


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=100, blank=True, null=True)
    action = models.CharField(max_length=50)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=100, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['action']),
            models.Index(fields=['user_id']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} on {self.entity_type} by {self.user_id}"


class Category(models.Model):
    CATEGORY_TYPES = [
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['type', 'name'], name='unique_category_type_name'),
        ]
        ordering = ['type', 'name']

    def __str__(self):
        return f"{self.name} ({self.type})"


class StudentIdCounter(models.Model):
    id = models.CharField(primary_key=True, max_length=20, default='singleton')
    prefix = models.CharField(max_length=10, default='S')
    next_value = models.IntegerField(default=1)
    pad_length = models.IntegerField(default=6)

    def __str__(self):
        return f"{self.prefix}{str(self.next_value).zfill(self.pad_length)}"
