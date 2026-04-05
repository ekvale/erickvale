from django.contrib import admin, messages

from .ai_categorize import categorize_capture_item
from .models import CaptureItem, RecurringCaptureRule


def _recategorize_captures_ai(modeladmin, request, queryset):
    """Re-run full AI pipeline (bounded batch)."""
    items = list(queryset.order_by('pk')[:40])
    if queryset.count() > len(items):
        modeladmin.message_user(
            request,
            f'Only the first {len(items)} selected items were processed (batch cap).',
            level=messages.WARNING,
        )
    for item in items:
        categorize_capture_item(item)
    modeladmin.message_user(
        request,
        f'Recategorized {len(items)} capture(s) with AI.',
        level=messages.SUCCESS,
    )


_recategorize_captures_ai.short_description = 'Recategorize selected captures with AI'


@admin.register(CaptureItem)
class CaptureItemAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'priority',
        'category_label',
        'is_actionable',
        'status',
        'gtd_bucket',
        'calendar_date',
        'calendar_is_hard_date',
        'archived',
        'created_at',
    )
    list_filter = (
        'status',
        'gtd_bucket',
        'priority',
        'archived',
        'is_actionable',
        'calendar_is_hard_date',
        'is_project',
    )
    search_fields = ('title', 'body', 'category_label', 'waiting_for', 'next_action')
    raw_id_fields = ('user',)
    readonly_fields = (
        'created_at',
        'updated_at',
        'ai_payload',
        'ai_error',
        'spawned_from_recurring',
    )
    date_hierarchy = 'created_at'
    actions = (_recategorize_captures_ai,)
    fieldsets = (
        (None, {'fields': ('user', 'body', 'title', 'category_label', 'priority')}),
        (
            'GTD clarify',
            {
                'fields': (
                    'is_actionable',
                    'non_actionable_disposition',
                    'is_project',
                    'next_action',
                    'engagement',
                    'two_minute_rule_suggested',
                )
            },
        ),
        (
            'Organize',
            {
                'fields': (
                    'gtd_bucket',
                    'status',
                    'waiting_for',
                    'calendar_date',
                    'calendar_is_hard_date',
                    'spawned_from_recurring',
                    'archived',
                    'completed_at',
                )
            },
        ),
        ('AI', {'fields': ('ai_payload', 'ai_error')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(RecurringCaptureRule)
class RecurringCaptureRuleAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'pattern',
        'next_run_date',
        'is_active',
        'last_spawned_at',
    )
    list_filter = ('is_active', 'pattern')
    search_fields = ('title', 'body')
    raw_id_fields = ('user',)
    readonly_fields = ('last_spawned_at', 'created_at', 'updated_at')
    date_hierarchy = 'next_run_date'
