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
    source_url_check_passed = models.BooleanField(
        null=True,
        blank=True,
        help_text='True if HTTP check passed, False if check failed (link may still be useful), null if not checked',
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


class LeaseCompResearchRun(models.Model):
    """LLM-generated lease / flex comparable memo (Bemidji-focused digest section)."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=GrantScoutRunStatus.choices,
        default=GrantScoutRunStatus.DRAFT,
    )
    coverage_summary = models.TextField(blank=True)
    search_query_log = models.JSONField(
        default=list,
        blank=True,
        help_text='Queries or topics the agent used',
    )
    compiled_report = models.TextField(
        blank=True,
        help_text='Plain-text memo for email and review',
    )
    agent_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text='Normalized agent payload',
    )
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lease comp research run'
        verbose_name_plural = 'Lease comp research runs'

    def __str__(self):
        return f'Lease comp {self.created_at.date()} ({self.get_status_display()})'


class BusinessCalendarEventType(models.TextChoices):
    """High-level buckets for the operations calendar (digest + future KPI agent)."""

    BILL = 'bill', 'Bill / recurring payment'
    LEASE = 'lease', 'Lease / occupancy'
    PROPERTY_TAX = 'property_tax', 'Property tax'
    INSURANCE = 'insurance', 'Insurance'
    LICENSE = 'license', 'License / permit'
    LOAN = 'loan', 'Loan / financing'
    MAINTENANCE = 'maintenance', 'Maintenance / capex'
    UTILITY = 'utility', 'Utility (electric, gas, etc.)'
    OTHER = 'other', 'Other'


class BusinessCalendarEvent(models.Model):
    """User- or import-maintained dates shown on the Dream Blue biweekly report."""

    title = models.CharField(max_length=200)
    event_type = models.CharField(
        max_length=32,
        choices=BusinessCalendarEventType.choices,
        default=BusinessCalendarEventType.OTHER,
    )
    due_date = models.DateField(
        db_index=True,
        help_text='Primary date (e.g. bill due, tax deadline, lease end)',
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text='Optional range end (e.g. renewal window)',
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Optional amount for cash-flow context',
    )
    property_label = models.CharField(
        max_length=128,
        blank=True,
        help_text='Building, parcel, or entity label',
    )
    notes = models.TextField(blank=True)
    interest_rate_annual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Annual interest rate % for loans (e.g. 7.50 for 7.5%)',
    )
    account_reference = models.CharField(
        max_length=120,
        blank=True,
        help_text='Utility account #, loan #, or similar',
    )
    contact_info = models.CharField(
        max_length=255,
        blank=True,
        help_text='Vendor / contact for this expense (phone, company name)',
    )
    reference_url = models.URLField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', 'sort_order', 'id']
        verbose_name = 'Business calendar event'
        verbose_name_plural = 'Business calendar events'

    def __str__(self):
        return f'{self.due_date}: {self.title[:50]}'


class BusinessKPIEntry(models.Model):
    """Key numbers shown on each report (maintain in admin; agents can sync later)."""

    label = models.CharField(max_length=120)
    value_display = models.CharField(
        max_length=120,
        help_text='Plain text, e.g. 12.4%, $42k, 3 units',
    )
    detail = models.TextField(
        blank=True,
        help_text='Optional short note / definition',
    )
    period_hint = models.CharField(
        max_length=64,
        blank=True,
        help_text='e.g. YTD 2026, Q1, trailing 12 mo',
    )
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Business KPI'
        verbose_name_plural = 'Business KPIs'

    def __str__(self):
        return f'{self.label}: {self.value_display}'


class BusinessReportSectionSource(models.TextChoices):
    MANUAL = 'manual', 'Manual / admin'
    AGENT = 'agent', 'Generated (future agent)'


class BusinessReportSection(models.Model):
    """
    Free-form narrative blocks for the combined report (manual now; LLM agent later).
    Upsert by slug from a management command when the KPI agent exists.
    """

    slug = models.SlugField(
        max_length=64,
        unique=True,
        help_text='Stable id, e.g. liquidity-summary, portfolio-outlook',
    )
    title = models.CharField(max_length=160)
    body = models.TextField(
        help_text='Plain text or light Markdown; rendered with line breaks in email',
    )
    source = models.CharField(
        max_length=20,
        choices=BusinessReportSectionSource.choices,
        default=BusinessReportSectionSource.MANUAL,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'slug']
        verbose_name = 'Business report section'
        verbose_name_plural = 'Business report sections'

    def __str__(self):
        return self.title
