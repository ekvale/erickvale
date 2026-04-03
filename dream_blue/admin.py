from django.contrib import admin

from .models import GrantScoutDriftEntry, GrantScoutOpportunity, GrantScoutRun


class GrantScoutOpportunityInline(admin.TabularInline):
    model = GrantScoutOpportunity
    extra = 0
    fields = (
        'category',
        'opportunity_type',
        'status',
        'deadline',
        'priority_score',
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
    search_fields = ('period_label', 'notes', 'coverage_summary')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [GrantScoutOpportunityInline, GrantScoutDriftEntryInline]
    fieldsets = (
        (None, {'fields': ('period_label', 'status', 'previous_run')}),
        ('Coverage', {'fields': ('coverage_summary', 'search_query_log', 'notes')}),
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
    )
    list_filter = ('category', 'status', 'run')
    search_fields = ('summary', 'opportunity_type', 'source_url', 'dedupe_key')
    raw_id_fields = ('run',)

    @admin.display(description='Summary')
    def summary_short(self, obj):
        return (obj.summary[:70] + '…') if len(obj.summary) > 70 else obj.summary


@admin.register(GrantScoutDriftEntry)
class GrantScoutDriftEntryAdmin(admin.ModelAdmin):
    list_display = ('summary_short', 'run', 'drift_type', 'opportunity', 'previous_opportunity')
    list_filter = ('drift_type',)
    search_fields = ('summary',)
    raw_id_fields = ('run', 'opportunity', 'previous_opportunity')

    @admin.display(description='Summary')
    def summary_short(self, obj):
        return (obj.summary[:60] + '…') if len(obj.summary) > 60 else obj.summary
