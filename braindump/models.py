import os

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


class TaskPriority(models.TextChoices):
    """AI + manual; lists sort urgent → high → normal → low."""

    URGENT = 'urgent', 'Urgent'
    HIGH = 'high', 'High'
    NORMAL = 'normal', 'Normal'
    LOW = 'low', 'Low'


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
        help_text='Work stream: MDH, Dream Blue, or Sioux Chef (auto from text on AI; editable)',
    )
    priority = models.CharField(
        max_length=16,
        choices=TaskPriority.choices,
        default=TaskPriority.NORMAL,
        db_index=True,
        help_text='Relative importance / time pressure (AI + editable)',
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

    spawned_from_recurring = models.ForeignKey(
        'RecurringCaptureRule',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='spawned_items',
    )


class RecurrencePattern(models.TextChoices):
    WEEKLY = 'weekly', 'Every week (same weekday)'
    EVERY_N_WEEKS = 'every_n_weeks', 'Every N weeks from anchor date'
    MONTHLY_LAST_WEEKDAY = 'monthly_last', 'Last Mon/Tue/… of each month'
    MONTHLY_NTH_WEEKDAY = 'monthly_nth', 'Nth weekday of month (1st–4th)'
    MONTHLY_DAY = 'monthly_day', 'Same calendar day each month'


class RecurringCaptureRule(models.Model):
    """Template that materializes a CaptureItem on each ``next_run_date`` (cron or morning digest)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='braindump_recurring_rules',
    )
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(help_text='Text for each spawned capture (AI clarifies)')
    is_active = models.BooleanField(default=True, db_index=True)
    pattern = models.CharField(max_length=32, choices=RecurrencePattern.choices)
    weekday = models.SmallIntegerField(
        null=True,
        blank=True,
        help_text='0=Monday … 6=Sunday (required for weekly / N-weeks / monthly weekday patterns)',
    )
    interval_weeks = models.PositiveSmallIntegerField(
        default=2,
        help_text='For “every N weeks” only (e.g. 2 = biweekly)',
    )
    nth_of_month = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text='1–4 for “nth weekday” (e.g. 2 = second Tuesday)',
    )
    day_of_month = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text='1–31 for “same day each month”',
    )
    anchor_date = models.DateField(
        help_text='Anchor: first due intent; every-N-weeks counts from here',
    )
    next_run_date = models.DateField(db_index=True)
    last_spawned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_run_date', 'pk']

    def __str__(self):
        return (self.title or self.body)[:50]

    def clean(self):
        from django.core.exceptions import ValidationError

        errs = {}
        wk_patterns = (
            RecurrencePattern.WEEKLY,
            RecurrencePattern.EVERY_N_WEEKS,
            RecurrencePattern.MONTHLY_LAST_WEEKDAY,
            RecurrencePattern.MONTHLY_NTH_WEEKDAY,
        )
        if self.pattern in wk_patterns and self.weekday is None:
            errs['weekday'] = 'Pick a weekday for this pattern.'
        if self.pattern == RecurrencePattern.MONTHLY_NTH_WEEKDAY:
            if self.nth_of_month is None or not (1 <= self.nth_of_month <= 4):
                errs['nth_of_month'] = 'Use 1–4 (e.g. 1 = first, 2 = second).'
        if self.pattern == RecurrencePattern.MONTHLY_DAY:
            if self.day_of_month is None or not (1 <= self.day_of_month <= 31):
                errs['day_of_month'] = 'Use a day 1–31.'
        if self.pattern == RecurrencePattern.EVERY_N_WEEKS:
            if not self.interval_weeks or self.interval_weeks < 1:
                errs['interval_weeks'] = 'Interval must be at least 1 week.'
        if errs:
            raise ValidationError(errs)


class ContactRelationshipKind(models.TextChoices):
    WORK = 'work', 'Work'
    PERSONAL = 'personal', 'Personal'
    BOTH = 'both', 'Work & personal'


class PersonalContact(models.Model):
    """Owner-only address book (work + personal)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='braindump_contacts',
    )
    display_name = models.CharField(max_length=200)
    first_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=64, blank=True)
    phone_secondary = models.CharField(max_length=64, blank=True)
    company = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=64, blank=True)
    postal_code = models.CharField(max_length=32, blank=True)
    country = models.CharField(max_length=120, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    relationship_kind = models.CharField(
        max_length=16,
        choices=ContactRelationshipKind.choices,
        default=ContactRelationshipKind.BOTH,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_name', 'pk']

    def __str__(self):
        return self.display_name


def contact_attachment_upload_to(instance, filename: str) -> str:
    return f'braindump_contacts/{instance.contact_id}/{filename}'


class PersonalContactAttachment(models.Model):
    contact = models.ForeignKey(
        PersonalContact,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    file = models.FileField(upload_to=contact_attachment_upload_to)
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at', 'pk']

    def display_label(self) -> str:
        if self.description:
            return self.description
        return os.path.basename(self.file.name)


class ContactScheduledEmail(models.Model):
    """Outbound message to a contact's email, queued for a future time or processed by cron/digest."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contact_scheduled_emails',
    )
    contact = models.ForeignKey(
        PersonalContact,
        on_delete=models.CASCADE,
        related_name='scheduled_emails',
    )
    subject = models.CharField(max_length=200)
    body = models.TextField()
    scheduled_for = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject[:40]} → {self.contact_id} ({self.status})'
