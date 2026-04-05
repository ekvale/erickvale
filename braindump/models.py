from django.conf import settings
from django.db import models
from django.utils import timezone


class GTDBucket(models.TextChoices):
    """Loose GTD-style buckets for AI + display."""

    NEXT_ACTION = 'next_action', 'Next action'
    PROJECT = 'project', 'Project (multi-step)'
    WAITING = 'waiting', 'Waiting for'
    SOMEDAY = 'someday', 'Someday / maybe'
    REFERENCE = 'reference', 'Reference'
    CALENDAR = 'calendar', 'Calendar / time-specific'


class CaptureStatus(models.TextChoices):
    OPEN = 'open', 'Still to do'
    WAITING = 'waiting', 'Waiting'
    DONE = 'done', 'Done'


class NonActionableDisposition(models.TextChoices):
    """Allen clarify step: if not actionable — trash, someday/maybe, or reference."""

    NONE = '', '—'
    TRASH = 'trash', 'Trash'
    SOMEDAY = 'someday', 'Someday / maybe'
    REFERENCE = 'reference', 'Reference'


class EngagementChoice(models.TextChoices):
    """Clarify: do now (incl. 2-min), defer to lists, or delegate (waiting)."""

    DO_NOW = 'do_now', 'Do now'
    DEFER = 'defer', 'Defer (next action list)'
    DELEGATE = 'delegate', 'Delegate / waiting'


class CaptureItem(models.Model):
    """One capture; AI clarifies (actionable?, next action, project?, calendar vs lists)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='braindump_items',
    )
    body = models.TextField(help_text='Raw capture text')
    title = models.CharField(max_length=200, blank=True, help_text='Short label from AI or you')
    category_label = models.CharField(
        max_length=120,
        blank=True,
        help_text='Free-form area, e.g. Home, Work',
    )
    gtd_bucket = models.CharField(
        max_length=32,
        choices=GTDBucket.choices,
        default=GTDBucket.NEXT_ACTION,
    )
    status = models.CharField(
        max_length=16,
        choices=CaptureStatus.choices,
        default=CaptureStatus.OPEN,
        db_index=True,
    )
    waiting_for = models.CharField(
        max_length=255,
        blank=True,
        help_text='Who / what you are waiting on',
    )
    calendar_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text=(
            'GTD: use only for time-specific actions (hard appointment/deadline). '
            'Generic next actions stay off the calendar.'
        ),
    )
    calendar_is_hard_date = models.BooleanField(
        default=False,
        db_index=True,
        help_text='True = belongs on calendar landscape; False = next-action list only',
    )
    is_actionable = models.BooleanField(
        null=True,
        blank=True,
        help_text='Clarify: is this actionable? null = not yet processed',
    )
    non_actionable_disposition = models.CharField(
        max_length=16,
        choices=NonActionableDisposition.choices,
        blank=True,
        default='',
        help_text='If not actionable: trash, someday, or reference',
    )
    is_project = models.BooleanField(
        default=False,
        help_text='True if multi-step outcome (project list)',
    )
    next_action = models.TextField(
        blank=True,
        help_text='Concrete next physical step (Allen)',
    )
    engagement = models.CharField(
        max_length=16,
        choices=EngagementChoice.choices,
        blank=True,
        default='',
        help_text='Do now, defer, or delegate',
    )
    two_minute_rule_suggested = models.BooleanField(
        default=False,
        help_text='AI thinks this may be a under-two-minute action',
    )
    archived = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Hidden from active inbox when done; still on calendar as completed',
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    ai_payload = models.JSONField(default=dict, blank=True)
    ai_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return (self.title or self.body)[:60]

    def mark_done(self):
        self.status = CaptureStatus.DONE
        self.archived = True
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'archived', 'completed_at', 'updated_at'])

    def mark_waiting(self, note: str = ''):
        self.status = CaptureStatus.WAITING
        self.gtd_bucket = GTDBucket.WAITING
        if note:
            self.waiting_for = note[:255]
        self.archived = False
        self.completed_at = None
        self.save(
            update_fields=[
                'status',
                'gtd_bucket',
                'waiting_for',
                'archived',
                'completed_at',
                'updated_at',
            ]
        )

    def mark_open(self):
        self.status = CaptureStatus.OPEN
        self.archived = False
        self.completed_at = None
        self.save(update_fields=['status', 'archived', 'completed_at', 'updated_at'])
