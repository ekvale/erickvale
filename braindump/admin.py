from django.contrib import admin

from .models import CaptureItem


@admin.register(CaptureItem)
class CaptureItemAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'status',
        'gtd_bucket',
        'calendar_date',
        'archived',
        'created_at',
    )
    list_filter = ('status', 'gtd_bucket', 'archived')
    search_fields = ('title', 'body', 'category_label', 'waiting_for')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at', 'ai_payload', 'ai_error')
    date_hierarchy = 'created_at'
