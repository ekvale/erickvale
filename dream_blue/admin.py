from django.contrib import admin

from .models import (
    BusinessBooksReconciliation,
    BusinessCalendarEvent,
    BusinessKPIEntry,
    BusinessReportSection,
    GrantScoutDriftEntry,
    GrantScoutOpportunity,
    GrantScoutRun,
    LeaseCompResearchRun,
    LeaseRentRollChange,
)


class GrantScoutOpportunityInline(admin.TabularInline):
    model = GrantScoutOpportunity
    extra = 0
    fields = (
        'category',
        'opportunity_type',
        'status',
        'deadline',
        'priority_score',
        'topic_tags',
        'source_url_check_passed',
        'summary',
        'source_url',
    )
    show_change_link = True


class GrantScoutDriftEntryInline(admin.TabularInline):
    model = GrantScoutDriftEntry
    extra = 0
    fk_name = 'run'
    fields = ('drift_type', 'opportunity', 'previous_opportunity', 'summary')


@admin.register(LeaseCompResearchRun)
class LeaseCompResearchRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created_at', 'previous_run', 'coverage_summary_preview')
    list_filter = ('status',)
    readonly_fields = (
        'created_at',
        'updated_at',
        'compiled_report',
        'agent_snapshot',
        'report_diff_summary',
    )
    raw_id_fields = ('previous_run',)
    search_fields = ('coverage_summary', 'compiled_report', 'error_message', 'report_diff_summary')

    @admin.display(description='Coverage')
    def coverage_summary_preview(self, obj):
        t = (obj.coverage_summary or '')[:80]
        return t + ('…' if len(obj.coverage_summary or '') > 80 else '')


@admin.register(GrantScoutRun)
class GrantScoutRunAdmin(admin.ModelAdmin):
    list_display = ('period_label', 'status', 'created_at', 'previous_run')
    list_filter = ('status',)
    search_fields = ('period_label', 'notes', 'coverage_summary', 'compiled_report')
    readonly_fields = ('created_at', 'updated_at', 'compiled_report', 'agent_snapshot')
    inlines = [GrantScoutOpportunityInline, GrantScoutDriftEntryInline]
    fieldsets = (
        (None, {'fields': ('period_label', 'status', 'previous_run')}),
        ('Coverage', {'fields': ('coverage_summary', 'search_query_log', 'notes')}),
        (
            'Stored report (from agent)',
            {
                'fields': ('compiled_report', 'agent_snapshot'),
                'description': 'Full text report and JSON snapshot written when grantscout_run_agent completes.',
            },
        ),
        ('Meta', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(GrantScoutOpportunity)
class GrantScoutOpportunityAdmin(admin.ModelAdmin):
    list_display = (
        'summary_short',
        'run',
        'category',
        'status',
        'priority_score',
        'deadline',
        'source_url_check_passed',
    )
    list_filter = ('category', 'status', 'run')
    search_fields = ('summary', 'opportunity_type', 'source_url', 'dedupe_key')
    raw_id_fields = ('run',)

    @admin.display(description='Summary')
    def summary_short(self, obj):
        return (obj.summary[:70] + '…') if len(obj.summary) > 70 else obj.summary


@admin.register(BusinessCalendarEvent)
class BusinessCalendarEventAdmin(admin.ModelAdmin):
    list_display = (
        'due_date',
        'title_short',
        'event_type',
        'property_label',
        'square_footage',
        'square_footage_storage',
        'amount',
        'rent_basis',
        'lease_doc_short',
        'interest_rate_annual',
        'refinance_date',
        'payoff_target_date',
        'account_reference_short',
        'is_active',
    )
    list_filter = ('event_type', 'is_active', 'rent_basis')
    search_fields = (
        'title',
        'property_label',
        'notes',
        'account_reference',
        'contact_info',
        'lease_document_url',
        'reference_url',
    )
    date_hierarchy = 'due_date'
    ordering = ('due_date', 'sort_order')

    @admin.display(description='Title')
    def title_short(self, obj):
        return (obj.title[:50] + '…') if len(obj.title) > 50 else obj.title

    @admin.display(description='Acct')
    def account_reference_short(self, obj):
        a = obj.account_reference or ''
        return (a[:18] + '…') if len(a) > 18 else a or '—'

    @admin.display(description='Lease doc')
    def lease_doc_short(self, obj):
        u = (getattr(obj, 'lease_document_url', None) or obj.reference_url or '').strip()
        if not u:
            return '—'
        return (u[:28] + '…') if len(u) > 28 else u


@admin.register(BusinessBooksReconciliation)
class BusinessBooksReconciliationAdmin(admin.ModelAdmin):
    list_display = (
        'period_label',
        'monthly_rent_income_books',
        'monthly_operating_expense_books',
        'is_active',
        'sort_order',
        'updated_at',
    )
    list_filter = ('is_active',)
    search_fields = ('period_label', 'variance_notes')


@admin.register(LeaseRentRollChange)
class LeaseRentRollChangeAdmin(admin.ModelAdmin):
    list_display = (
        'recorded_at',
        'event',
        'amount_before',
        'amount_after',
        'square_footage_before',
        'square_footage_after',
        'source',
    )
    list_filter = ('source',)
    search_fields = ('event__title', 'event__property_label')
    raw_id_fields = ('event',)
    readonly_fields = ('recorded_at',)


@admin.register(BusinessKPIEntry)
class BusinessKPIEntryAdmin(admin.ModelAdmin):
    list_display = ('label', 'value_display', 'period_hint', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('label', 'detail')


@admin.register(BusinessReportSection)
class BusinessReportSectionAdmin(admin.ModelAdmin):
    list_display = ('slug', 'title', 'source', 'is_active', 'sort_order', 'updated_at')
    list_filter = ('source', 'is_active')
    search_fields = ('slug', 'title', 'body')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(GrantScoutDriftEntry)
class GrantScoutDriftEntryAdmin(admin.ModelAdmin):
    list_display = ('summary_short', 'run', 'drift_type', 'opportunity', 'previous_opportunity')
    list_filter = ('drift_type',)
    search_fields = ('summary',)
    raw_id_fields = ('run', 'opportunity', 'previous_opportunity')

    @admin.display(description='Summary')
    def summary_short(self, obj):
        return (obj.summary[:60] + '…') if len(obj.summary) > 60 else obj.summary
