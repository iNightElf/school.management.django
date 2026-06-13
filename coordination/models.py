import uuid
from django.db import models


class Alert(models.Model):
    ALERT_TYPES = [
        ('attendance', 'Attendance'),
        ('academic', 'Academic'),
        ('behavior', 'Behavior'),
        ('parent', 'Parent'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
    ]
    SEVERITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='coordination_alerts'
    )
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='created_alerts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['alert_type', 'status']),
            models.Index(fields=['student']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_alert_type_display()})"


class Intervention(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert = models.ForeignKey(
        Alert, on_delete=models.CASCADE,
        related_name='interventions'
    )
    action_taken = models.TextField()
    followup_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='created_interventions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Intervention'
        verbose_name_plural = 'Interventions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'followup_date']),
            models.Index(fields=['alert']),
        ]

    def __str__(self):
        return f"Intervention for {self.alert.title}"


class ParentCommunication(models.Model):
    TYPE_CHOICES = [
        ('call', 'Call'),
        ('meeting', 'Meeting'),
        ('complaint', 'Complaint'),
        ('follow_up', 'Follow Up'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='parent_communications'
    )
    communication_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    notes = models.TextField()
    followup_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='created_communications'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Parent Communication'
        verbose_name_plural = 'Parent Communications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_communication_type_display()} - {self.student.name}"


class TeacherWeeklyReport(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class_teacher = models.ForeignKey(
        'teachers.ClassTeacher', on_delete=models.CASCADE,
        related_name='weekly_reports'
    )
    week_start_date = models.DateField()
    attendance_notes = models.TextField(blank=True, default='')
    academics_notes = models.TextField(blank=True, default='')
    behavior_notes = models.TextField(blank=True, default='')
    parent_issues_notes = models.TextField(blank=True, default='')
    recognition_notes = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Teacher Weekly Report'
        verbose_name_plural = 'Teacher Weekly Reports'
        ordering = ['-week_start_date']
        constraints = [
            models.UniqueConstraint(
                fields=['class_teacher', 'week_start_date'],
                name='unique_report_per_teacher_week'
            ),
        ]
        indexes = [
            models.Index(fields=['week_start_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Report by {self.class_teacher.teacher.name} - {self.week_start_date}"


class ClassTest(models.Model):
    TERM_CHOICES = [
        ('1', '1st Term'),
        ('2', '2nd Term'),
        ('3', '3rd Term'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_class = models.ForeignKey(
        'core.SchoolClass', on_delete=models.CASCADE,
        related_name='class_tests'
    )
    subject = models.ForeignKey(
        'core.Subject', on_delete=models.CASCADE,
        related_name='class_tests'
    )
    term = models.CharField(max_length=10, choices=TERM_CHOICES, default='1')
    test_name = models.CharField(max_length=255)
    test_date = models.DateField()
    total_marks = models.PositiveIntegerField()
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='created_class_tests'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Class Test'
        verbose_name_plural = 'Class Tests'
        ordering = ['-test_date']
        constraints = [
            models.UniqueConstraint(
                fields=['school_class', 'subject', 'test_name', 'term'],
                name='unique_test_per_class_subject_name_term'
            ),
        ]
        indexes = [
            models.Index(fields=['school_class', 'subject', 'term']),
            models.Index(fields=['test_date']),
        ]

    def __str__(self):
        return f"{self.test_name} - {self.school_class.name} ({self.subject.name}) [{self.get_term_display()}]"


class ClassTestMark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class_test = models.ForeignKey(
        ClassTest, on_delete=models.CASCADE,
        related_name='marks'
    )
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='class_test_marks'
    )
    marks_obtained = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Class Test Mark'
        verbose_name_plural = 'Class Test Marks'
        constraints = [
            models.UniqueConstraint(
                fields=['class_test', 'student'],
                name='unique_mark_per_student_per_test'
            ),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.marks_obtained}/{self.class_test.total_marks}"


class CoordinatorTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_tasks'
    )
    related_alert = models.ForeignKey(
        Alert, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tasks'
    )
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='created_tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Coordinator Task'
        verbose_name_plural = 'Coordinator Tasks'
        ordering = ['due_date', '-priority']
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['assigned_to']),
        ]

    def __str__(self):
        return self.title
