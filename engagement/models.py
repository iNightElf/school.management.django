import uuid
from django.db import models
from django.conf import settings


class DailyQuiz(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1)
    category = models.CharField(max_length=50, default='general')
    quiz_date = models.DateField(unique=True)
    explanation = models.TextField(blank=True, default='')
    generated_by = models.CharField(max_length=20, default='ai')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Daily Quiz'
        verbose_name_plural = 'Daily Quizzes'
        ordering = ['-quiz_date']

    def __str__(self):
        return f"Quiz {self.quiz_date}: {self.question[:50]}"


class QuizResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_responses')
    question = models.ForeignKey(DailyQuiz, on_delete=models.CASCADE, related_name='responses')
    selected_answer = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Quiz Response'
        verbose_name_plural = 'Quiz Responses'
        unique_together = ['user', 'question']

    def __str__(self):
        return f"{self.user.name} - {self.question.quiz_date} - {'✓' if self.is_correct else '✗'}"


class DailyRiddle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField()
    hint = models.TextField(blank=True, default='')
    answer = models.CharField(max_length=255)
    riddle_date = models.DateField(unique=True)
    generated_by = models.CharField(max_length=20, default='ai')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Daily Riddle'
        verbose_name_plural = 'Daily Riddles'
        ordering = ['-riddle_date']

    def __str__(self):
        return f"Riddle {self.riddle_date}"


class RiddleResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='riddle_responses')
    riddle = models.ForeignKey(DailyRiddle, on_delete=models.CASCADE, related_name='responses')
    guess = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Riddle Response'
        verbose_name_plural = 'Riddle Responses'
        unique_together = ['user', 'riddle']

    def __str__(self):
        return f"{self.user.name} - {self.riddle.riddle_date} - {'✓' if self.is_correct else '✗'}"


class DailyTip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tip = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('classroom', 'Classroom Management'),
        ('assessment', 'Assessment'),
        ('engagement', 'Student Engagement'),
        ('general', 'General'),
    ])
    tip_date = models.DateField()
    generated_by = models.CharField(max_length=20, default='ai')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Daily Tip'
        verbose_name_plural = 'Daily Tips'
        unique_together = ['tip_date', 'category']
        ordering = ['-tip_date']

    def __str__(self):
        return f"Tip {self.tip_date} ({self.category})"


class WeeklyChallenge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    challenge_type = models.CharField(max_length=20, choices=[
        ('text', 'Text Response'),
        ('emoji', 'Emoji Rating'),
    ])
    is_active = models.BooleanField(default=True)
    start_date = models.DateField()
    end_date = models.DateField()
    generated_by = models.CharField(max_length=20, default='ai')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Weekly Challenge'
        verbose_name_plural = 'Weekly Challenges'
        ordering = ['-start_date']

    def __str__(self):
        return f"Challenge: {self.title}"


class ChallengeResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='challenge_responses')
    challenge = models.ForeignKey(WeeklyChallenge, on_delete=models.CASCADE, related_name='responses')
    text_response = models.TextField(blank=True, default='')
    emoji_response = models.CharField(max_length=10, blank=True, default='')
    responded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Challenge Response'
        verbose_name_plural = 'Challenge Responses'
        unique_together = ['user', 'challenge']

    def __str__(self):
        return f"{self.user.name} - {self.challenge.title[:30]}"


class MoodCheckin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mood_checkins')
    mood = models.IntegerField(choices=[
        (1, 'Terrible'),
        (2, 'Bad'),
        (3, 'Okay'),
        (4, 'Good'),
        (5, 'Great'),
    ])
    checkin_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mood Checkin'
        verbose_name_plural = 'Mood Checkins'
        unique_together = ['user', 'checkin_date']

    def __str__(self):
        return f"{self.user.name} - {self.checkin_date} - {self.get_mood_display()}"


class LessonPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_plans')
    plan_date = models.DateField()
    class_name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Lesson Plan'
        verbose_name_plural = 'Lesson Plans'
        unique_together = ['user', 'plan_date', 'class_name', 'subject']
        ordering = ['-plan_date']

    def __str__(self):
        return f"{self.user.name} - {self.plan_date} - {self.subject}"


class TeacherStreak(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_streak')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    total_days_active = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Teacher Streak'
        verbose_name_plural = 'Teacher Streaks'

    def __str__(self):
        return f"{self.user.name} - {self.current_streak} day streak"
