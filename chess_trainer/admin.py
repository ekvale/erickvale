from django.contrib import admin
from .models import Opening, Lesson, UserProgress, UserStats


@admin.register(Opening)
class OpeningAdmin(admin.ModelAdmin):
    list_display = ['name', 'side', 'eco_code']
    list_filter = ['side']
    search_fields = ['name', 'eco_code']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'opening', 'lesson_type', 'order']
    list_filter = ['lesson_type', 'opening']
    ordering = ['opening', 'order']


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'completed', 'score', 'attempts', 'last_attempted']
    list_filter = ['completed', 'lesson__opening']
    search_fields = ['user__username']


@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'opening', 'mastery_pct', 'streak', 'next_review_date']
    list_filter = ['opening']
    search_fields = ['user__username']
