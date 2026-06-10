from django.contrib import admin
from .models import (
    DailyQuiz, QuizResponse, DailyRiddle, RiddleResponse,
    DailyTip, WeeklyChallenge, ChallengeResponse, MoodCheckin,
    LessonPlan, TeacherStreak,
)


@admin.register(DailyQuiz)
class DailyQuizAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'quiz_date', 'generated_by')
    list_filter = ('category', 'generated_by')
    search_fields = ('question',)
    readonly_fields = ('id', 'created_at')


@admin.register(QuizResponse)
class QuizResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'selected_answer', 'is_correct', 'answered_at')
    list_filter = ('is_correct',)
    readonly_fields = ('id', 'answered_at')


@admin.register(DailyRiddle)
class DailyRiddleAdmin(admin.ModelAdmin):
    list_display = ('question', 'riddle_date', 'generated_by')
    list_filter = ('generated_by',)
    readonly_fields = ('id', 'created_at')


@admin.register(RiddleResponse)
class RiddleResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'riddle', 'guess', 'is_correct', 'answered_at')
    list_filter = ('is_correct',)
    readonly_fields = ('id', 'answered_at')


@admin.register(DailyTip)
class DailyTipAdmin(admin.ModelAdmin):
    list_display = ('tip', 'category', 'tip_date', 'generated_by')
    list_filter = ('category', 'generated_by')
    readonly_fields = ('id', 'created_at')


@admin.register(WeeklyChallenge)
class WeeklyChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'challenge_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('challenge_type', 'is_active')
    readonly_fields = ('id', 'created_at')


@admin.register(ChallengeResponse)
class ChallengeResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'text_response', 'emoji_response', 'responded_at')
    readonly_fields = ('id', 'responded_at')


@admin.register(MoodCheckin)
class MoodCheckinAdmin(admin.ModelAdmin):
    list_display = ('user', 'mood', 'checkin_date')
    list_filter = ('mood',)
    readonly_fields = ('id', 'created_at')


@admin.register(LessonPlan)
class LessonPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_date', 'class_name', 'subject')
    list_filter = ('plan_date',)
    readonly_fields = ('id', 'created_at')


@admin.register(TeacherStreak)
class TeacherStreakAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'longest_streak', 'last_active_date', 'total_days_active')
    readonly_fields = ('id', 'created_at', 'updated_at')
