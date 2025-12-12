"""
Admin interface for literary analysis app.
"""
from django.contrib import admin
from .models import LiteraryWork, CodebookTemplate, Code, Analysis, CodedSegment, AnalyticalMemo


@admin.register(LiteraryWork)
class LiteraryWorkAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'uploaded_by', 'uploaded_at', 'text_length']
    list_filter = ['uploaded_at', 'author']
    search_fields = ['title', 'author']
    readonly_fields = ['uploaded_at', 'text_length']


@admin.register(CodebookTemplate)
class CodebookTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_public', 'created_by', 'created_at']
    list_filter = ['template_type', 'is_public', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Code)
class CodeAdmin(admin.ModelAdmin):
    list_display = ['code_name', 'codebook', 'code_type', 'parent_code', 'order']
    list_filter = ['code_type', 'codebook']
    search_fields = ['code_name', 'definition']
    ordering = ['codebook', 'order', 'code_name']


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ['literary_work', 'codebook', 'analyst', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'codebook']
    search_fields = ['literary_work__title', 'codebook__name']
    readonly_fields = ['created_at', 'updated_at', 'report_generated_at']


@admin.register(CodedSegment)
class CodedSegmentAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'start_position', 'end_position', 'location', 'created_by', 'created_at']
    list_filter = ['created_at', 'analysis']
    search_fields = ['text_excerpt', 'location', 'memo']
    filter_horizontal = ['codes']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AnalyticalMemo)
class AnalyticalMemoAdmin(admin.ModelAdmin):
    list_display = ['title', 'analysis', 'created_by', 'created_at']
    list_filter = ['created_at', 'analysis']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
