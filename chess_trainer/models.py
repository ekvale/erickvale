"""
Chess Opening Trainer models.
"""
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import math


class Opening(models.Model):
    """Chess opening (e.g. Scotch Game, Sicilian Najdorf)."""
    SIDE_CHOICES = [('white', 'White'), ('black', 'Black')]
    name = models.CharField(max_length=200)
    side = models.CharField(max_length=10, choices=SIDE_CHOICES)
    eco_code = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    move_sequence = models.JSONField(
        default=list,
        help_text='List of [white_move, black_move] pairs, e.g. [["e4","e5"],["Nf3","Nc6"]]'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.side})"

    def get_absolute_url(self):
        return reverse('chess_trainer:opening_detail', kwargs={'pk': self.pk})


class Lesson(models.Model):
    """Lesson for an opening (concept, drill, or quiz)."""
    LESSON_TYPE_CHOICES = [
        ('concept', 'Concept'),
        ('drill', 'Drill'),
        ('quiz', 'Quiz'),
    ]
    opening = models.ForeignKey(Opening, on_delete=models.CASCADE, related_name='lessons')
    order = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=200)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES)
    content = models.JSONField(
        default=dict,
        help_text='Key ideas, critical moves, common mistakes, tactical themes, quiz/drill config'
    )

    class Meta:
        ordering = ['opening', 'order']
        unique_together = [['opening', 'order']]

    def __str__(self):
        return f"{self.opening.name}: {self.title} ({self.lesson_type})"

    def get_absolute_url(self):
        return reverse('chess_trainer:lesson', kwargs={'pk': self.pk})


class UserProgress(models.Model):
    """Tracks a user's completion of a lesson."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chess_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='user_progress')
    completed = models.BooleanField(default=False)
    score = models.PositiveIntegerField(default=0, help_text='Score out of 100 for quiz/drill')
    attempts = models.PositiveIntegerField(default=0)
    last_attempted = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['user', 'lesson']]
        verbose_name_plural = 'User progress'

    def __str__(self):
        return f"{self.user.username} - {self.lesson} ({'completed' if self.completed else 'in progress'})"


class UserStats(models.Model):
    """Per-opening stats for spaced repetition (SM-2 style)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chess_stats')
    opening = models.ForeignKey(Opening, on_delete=models.CASCADE, related_name='user_stats')
    mastery_pct = models.FloatField(default=0.0, help_text='0-100')
    streak = models.PositiveIntegerField(default=0, help_text='Days practiced in a row')
    last_practiced = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    ease_factor = models.FloatField(default=2.5)
    interval_days = models.PositiveIntegerField(default=1)
    repetitions = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['user', 'opening']]
        verbose_name_plural = 'User stats'

    def __str__(self):
        return f"{self.user.username} - {self.opening.name}: {self.mastery_pct:.0f}%"

    def update_spaced_repetition(self, correct: bool):
        """Simple SM-2-style update: correct answers increase interval, wrong ones reset."""
        today = timezone.now().date()
        self.last_practiced = today
        self.repetitions += 1

        if correct:
            # Increase mastery
            self.mastery_pct = min(100, self.mastery_pct + 5)
            # Increase interval for next review
            self.interval_days = max(1, int(self.interval_days * 1.5) if self.repetitions > 1 else 1)
            self.ease_factor = min(2.5, self.ease_factor + 0.1)
            self.next_review_date = today + timedelta(days=self.interval_days)
        else:
            # Decrease mastery
            self.mastery_pct = max(0, self.mastery_pct - 3)
            # Reset interval
            self.interval_days = 1
            self.ease_factor = max(1.3, self.ease_factor - 0.2)
            self.next_review_date = today  # Review again tomorrow
        self.save()
