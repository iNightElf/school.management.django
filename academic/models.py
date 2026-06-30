import uuid
from django.db import models
from django.conf import settings


class RoutineTemplate(models.Model):
    DAY_CHOICES = [
        ('sunday', 'Sunday'), ('monday', 'Monday'), ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'), ('thursday', 'Thursday'),
        ('friday', 'Friday'), ('saturday', 'Saturday'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_class = models.ForeignKey(
        'core.SchoolClass', on_delete=models.CASCADE, related_name='routines',
    )
    section = models.CharField(max_length=50, blank=True, default='')
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    period_number = models.IntegerField()
    subject = models.ForeignKey(
        'core.Subject', on_delete=models.CASCADE, related_name='routines',
    )
    teacher = models.ForeignKey(
        'teachers.Teacher', on_delete=models.CASCADE, related_name='routines',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['school_class', 'section', 'day', 'period_number']
        constraints = [
            models.UniqueConstraint(
                fields=['school_class', 'section', 'day', 'period_number'],
                name='unique_period_per_day',
            ),
        ]
        verbose_name = 'Routine Template'
        verbose_name_plural = 'Routine Templates'

    def __str__(self):
        return f"{self.school_class.name} {self.day} P{self.period_number}"


class LessonPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    routine_template = models.ForeignKey(
        RoutineTemplate, on_delete=models.CASCADE, related_name='lesson_plans',
    )
    week_start = models.DateField()
    topic = models.CharField(max_length=500)
    learning_objectives = models.TextField(blank=True, default='')
    activities = models.TextField(blank=True, default='')
    materials = models.TextField(blank=True, default='')
    assessment = models.TextField(blank=True, default='')
    remarks = models.TextField(blank=True, default='')
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['week_start', 'routine_template__period_number']
        constraints = [
            models.UniqueConstraint(
                fields=['routine_template', 'week_start'],
                name='unique_lesson_plan_per_week',
            ),
        ]
        verbose_name = 'Lesson Plan'
        verbose_name_plural = 'Lesson Plans'

    def __str__(self):
        return f"{self.routine_template.subject.name} wk {self.week_start}"


class Homework(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_class = models.ForeignKey(
        'core.SchoolClass', on_delete=models.CASCADE, related_name='homeworks',
    )
    section = models.CharField(max_length=50, blank=True, default='')
    subject = models.ForeignKey(
        'core.Subject', on_delete=models.CASCADE, related_name='homeworks',
    )
    teacher = models.ForeignKey(
        'teachers.Teacher', on_delete=models.CASCADE, related_name='homeworks',
    )
    date = models.DateField()
    topic = models.CharField(max_length=500)
    description = models.TextField()
    due_date = models.DateField()
    attachment = models.TextField(blank=True, default='')
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Homework'
        verbose_name_plural = 'Homeworks'

    def __str__(self):
        return f"{self.subject.name} - {self.date}"


class Diary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_class = models.ForeignKey(
        'core.SchoolClass', on_delete=models.CASCADE, related_name='diaries',
    )
    section = models.CharField(max_length=50, blank=True, default='')
    subject = models.ForeignKey(
        'core.Subject', on_delete=models.CASCADE, related_name='diaries',
    )
    teacher = models.ForeignKey(
        'teachers.Teacher', on_delete=models.CASCADE, related_name='diaries',
    )
    date = models.DateField()
    topic = models.CharField(max_length=500)
    activities = models.TextField(blank=True, default='')
    remarks = models.TextField(blank=True, default='')
    attachment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Diary'
        verbose_name_plural = 'Diaries'

    def __str__(self):
        return f"{self.subject.name} - {self.date}"


class ExamRoutine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam_name = models.CharField(max_length=255)
    school_class = models.ForeignKey(
        'core.SchoolClass', on_delete=models.CASCADE, related_name='exam_routines',
    )
    section = models.CharField(max_length=50, blank=True, default='')
    subject = models.ForeignKey(
        'core.Subject', on_delete=models.CASCADE, related_name='exam_routines',
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    room = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['exam_name', 'school_class', 'section', 'subject'],
                name='unique_exam_subject_per_class',
            ),
        ]
        verbose_name = 'Exam Routine'
        verbose_name_plural = 'Exam Routines'

    def __str__(self):
        return f"{self.exam_name} - {self.subject.name}"
