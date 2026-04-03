from django.contrib import admin

from .models import (
    BusinessCalendarEvent,
    BusinessKPIEntry,
    BusinessReportSection,
    GrantScoutDriftEntry,
    GrantScoutOpportunity,
    GrantScoutRun,
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
        'amount',
        'is_active',
    )
    list_filter = ('event_type', 'is_active')
    search_fields = ('title', 'property_label', 'notes')
    date_hierarchy = 'due_date'
    ordering = ('due_date', 'sort_order')

    @admin.display(description='Title')
    def title_short(self, obj):
        return (obj.title[:50] + '…') if len(obj.title) > 50 else obj.title


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
