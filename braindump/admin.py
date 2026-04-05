from django.contrib import admin

from .models import CaptureItem


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
    readonly_fields = ('created_at', 'updated_at', 'ai_payload', 'ai_error')
    date_hierarchy = 'created_at'
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
                    'archived',
                    'completed_at',
                )
            },
        ),
        ('AI', {'fields': ('ai_payload', 'ai_error')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
