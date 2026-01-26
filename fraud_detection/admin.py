from django.contrib import admin
from .models import (
    Transaction, Vendor, Contract, FraudFlag, BudgetRecord,
    Department, BudgetCategory, AnalysisResult
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['created_at']


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent']
    search_fields = ['name', 'code']
    list_filter = ['parent']


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'registration_number', 'created_at']
    search_fields = ['name', 'registration_number', 'address']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'date', 'amount', 'vendor', 'department', 'status', 'created_at']
    list_filter = ['status', 'date', 'fiscal_year', 'department', 'category']
    search_fields = ['transaction_id', 'description', 'invoice_number', 'contract_number', 'vendor__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'date', 'amount', 'description', 'status')
        }),
        ('Relationships', {
            'fields': ('vendor', 'department', 'category')
        }),
        ('Additional Information', {
            'fields': ('fiscal_year', 'invoice_number', 'contract_number', 'location')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['contract_number', 'title', 'vendor', 'department', 'total_amount', 'start_date']
    list_filter = ['start_date', 'department']
    search_fields = ['contract_number', 'title', 'vendor__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(BudgetRecord)
class BudgetRecordAdmin(admin.ModelAdmin):
    list_display = ['department', 'category', 'fiscal_year', 'allocated_amount']
    list_filter = ['fiscal_year', 'department']
    search_fields = ['department__name', 'category__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FraudFlag)
class FraudFlagAdmin(admin.ModelAdmin):
    list_display = ['title', 'flag_type', 'risk_level', 'status', 'detected_at']
    list_filter = ['flag_type', 'risk_level', 'status', 'detected_at']
    search_fields = ['title', 'description']
    filter_horizontal = ['transactions', 'vendors', 'contracts']
    readonly_fields = ['detected_at']
    fieldsets = (
        ('Flag Information', {
            'fields': ('flag_type', 'risk_level', 'title', 'description', 'status')
        }),
        ('Related Objects', {
            'fields': ('transactions', 'vendors', 'contracts')
        }),
        ('Resolution', {
            'fields': ('resolved_at', 'resolved_by', 'notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('detected_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ['analysis_type', 'status', 'flags_created', 'started_at', 'completed_at']
    list_filter = ['analysis_type', 'status', 'started_at']
    search_fields = ['summary', 'error_message']
    readonly_fields = ['started_at', 'completed_at']
    fieldsets = (
        ('Analysis Information', {
            'fields': ('analysis_type', 'status', 'run_by')
        }),
        ('Results', {
            'fields': ('flags_created', 'transactions_analyzed', 'summary', 'error_message')
        }),
        ('Parameters', {
            'fields': ('parameters',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
