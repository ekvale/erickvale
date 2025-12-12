"""
Admin interface for literary analysis app.
"""
from django.contrib import admin
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms
from .models import LiteraryWork, CodebookTemplate, Code, Analysis, CodedSegment, AnalyticalMemo


@admin.register(LiteraryWork)
class LiteraryWorkAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'uploaded_by', 'uploaded_at', 'text_length']
    list_filter = ['uploaded_at', 'author']
    search_fields = ['title', 'author']
    readonly_fields = ['uploaded_at', 'text_length']


class CodeInline(admin.TabularInline):
    """Inline editor for codes within a codebook."""
    model = Code
    extra = 1
    fields = ['code_name', 'code_type', 'definition', 'parent_code', 'order']
    ordering = ['order', 'code_name']
    autocomplete_fields = ['parent_code']
    verbose_name = 'Code'
    verbose_name_plural = 'Codes'


@admin.register(CodebookTemplate)
class CodebookTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_public', 'created_by', 'created_at', 'code_count']
    list_filter = ['template_type', 'is_public', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CodeInline]
    
    def code_count(self, obj):
        """Display the number of codes in this codebook."""
        return obj.codes.count()
    code_count.short_description = 'Codes'


@admin.register(Code)
class CodeAdmin(admin.ModelAdmin):
    list_display = ['code_name', 'codebook', 'code_type', 'parent_code', 'order', 'subcode_count']
    list_filter = ['code_type', 'codebook']
    search_fields = ['code_name', 'definition']
    ordering = ['codebook', 'order', 'code_name']
    autocomplete_fields = ['parent_code', 'codebook']
    fieldsets = (
        ('Basic Information', {
            'fields': ('codebook', 'code_name', 'code_type', 'definition')
        }),
        ('Organization', {
            'fields': ('parent_code', 'order'),
            'description': 'Set parent_code to create hierarchical relationships. Order controls display sequence.'
        }),
        ('Examples', {
            'fields': ('examples',),
            'classes': ('collapse',),
        }),
    )
    
    def subcode_count(self, obj):
        """Display the number of subcodes under this code."""
        return obj.subcodes.count()
    subcode_count.short_description = 'Subcodes'


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ['literary_work', 'codebook', 'analyst', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'codebook']
    search_fields = ['literary_work__title', 'codebook__name']
    readonly_fields = ['created_at', 'updated_at', 'report_generated_at']


class CodedSegmentAdminForm(forms.ModelForm):
    class Meta:
        model = CodedSegment
        fields = '__all__'
        widgets = {
            'memo': CKEditorUploadingWidget(config_name='default'),
        }


@admin.register(CodedSegment)
class CodedSegmentAdmin(admin.ModelAdmin):
    form = CodedSegmentAdminForm
    list_display = ['analysis', 'start_position', 'end_position', 'location', 'created_by', 'created_at']
    list_filter = ['created_at', 'analysis']
    search_fields = ['text_excerpt', 'location', 'memo']
    filter_horizontal = ['codes']
    readonly_fields = ['created_at', 'updated_at']


class AnalyticalMemoAdminForm(forms.ModelForm):
    class Meta:
        model = AnalyticalMemo
        fields = '__all__'
        widgets = {
            'content': CKEditorUploadingWidget(config_name='default'),
        }


@admin.register(AnalyticalMemo)
class AnalyticalMemoAdmin(admin.ModelAdmin):
    form = AnalyticalMemoAdminForm
    list_display = ['title', 'analysis', 'created_by', 'created_at']
    list_filter = ['created_at', 'analysis']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
