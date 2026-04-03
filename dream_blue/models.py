from django.db import models
from django.utils import timezone


class GrantScoutRunStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class GrantScoutCategory(models.TextChoices):
    GRANT = 'grant', 'Grant'
    TAX_CREDIT = 'tax_credit', 'Tax credit'
    REBATE = 'rebate', 'Rebate'
    REGULATORY = 'regulatory', 'Regulatory / compliance'
    OTHER = 'other', 'Other'


class GrantScoutOpportunityStatus(models.TextChoices):
    NEW = 'new', 'New'
    TRACKING = 'tracking', 'Tracking'
    APPLIED = 'applied', 'Applied'
    CLOSED = 'closed', 'Closed'
    EXPIRED = 'expired', 'Expired'


class GrantScoutDriftType(models.TextChoices):
    NEW = 'new', 'New vs previous run'
    UPDATED = 'updated', 'Updated vs previous run'
    REMOVED = 'removed', 'Removed since previous run'


class GrantScoutRun(models.Model):
    """One monthly (or ad hoc) GrantScout research run."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    period_label = models.CharField(
        max_length=32,
        help_text='e.g. 2026-03 for March 2026',
    )
    status = models.CharField(
        max_length=20,
        choices=GrantScoutRunStatus.choices,
        default=GrantScoutRunStatus.DRAFT,
    )
    previous_run = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='next_runs',
        help_text='Prior run used for drift comparison',
    )
    search_query_log = models.JSONField(
        default=list,
        blank=True,
        help_text='List of queries or steps performed (for audit)',
    )
    coverage_summary = models.TextField(
        blank=True,
        help_text='Short narrative of jurisdictions/topics covered',
    )
    compiled_report = models.TextField(
        blank=True,
        help_text='Full human-readable report (Markdown) generated when the agent runs',
    )
    agent_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text='Full normalized agent payload (audit / re-import)',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'GrantScout run'
        verbose_name_plural = 'GrantScout runs'

    def __str__(self):
        return f'{self.period_label} ({self.get_status_display()})'


class GrantScoutOpportunity(models.Model):
    """A single funding, incentive, or regulatory signal from a run."""

    run = models.ForeignKey(
        GrantScoutRun,
        on_delete=models.CASCADE,
        related_name='opportunities',
    )
    category = models.CharField(
        max_length=32,
        choices=GrantScoutCategory.choices,
        default=GrantScoutCategory.OTHER,
    )
    opportunity_type = models.CharField(
        max_length=128,
        blank=True,
        help_text='Subtype label, e.g. DEED program name',
    )
    eligibility = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=GrantScoutOpportunityStatus.choices,
        default=GrantScoutOpportunityStatus.NEW,
    )
    deadline = models.DateField(null=True, blank=True)
    summary = models.TextField()
    action_recommended = models.TextField(blank=True)
    source_url = models.URLField(max_length=500)
    priority_score = models.IntegerField(
        default=0,
        help_text='Higher = more important for dashboard/digest',
    )
    dedupe_key = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text='Stable id across runs (e.g. hash of canonical URL)',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority_score', '-created_at']
        verbose_name = 'GrantScout opportunity'
        verbose_name_plural = 'GrantScout opportunities'

    def __str__(self):
        return f'{self.get_category_display()}: {self.summary[:60]}'


class GrantScoutDriftEntry(models.Model):
    """Optional comparison row vs previous_run on the same GrantScoutRun."""

    run = models.ForeignKey(
        GrantScoutRun,
        on_delete=models.CASCADE,
        related_name='drift_entries',
    )
    drift_type = models.CharField(
        max_length=20,
        choices=GrantScoutDriftType.choices,
    )
    opportunity = models.ForeignKey(
        GrantScoutOpportunity,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='drift_entries',
        help_text='Current-run opportunity when new or updated',
    )
    previous_opportunity = models.ForeignKey(
        GrantScoutOpportunity,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='drift_entries_as_previous',
        help_text='Prior-run row for updated/removed',
    )
    summary = models.CharField(max_length=500)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['drift_type', 'id']
        verbose_name = 'GrantScout drift entry'
        verbose_name_plural = 'GrantScout drift entries'

    def __str__(self):
        return f'{self.get_drift_type_display()}: {self.summary[:80]}'
