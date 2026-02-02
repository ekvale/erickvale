"""
Django admin for All Minnesota models.
"""
from django.contrib import admin
from .models import (
    Contact,
    DistributionSite,
    BusinessPlan,
    PlanSection,
    KPI,
    KPIUpdateHistory,
    Task,
    SocialMediaPost,
)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'email', 'contact_type', 'is_active', 'date_added']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'notes']
    list_filter = ['contact_type', 'is_active', 'date_added']
    readonly_fields = ['date_added']
    raw_id_fields = ['created_by']


@admin.register(DistributionSite)
class DistributionSiteAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'region', 'city', 'capacity', 'is_active', 'date_added']
    search_fields = ['site_name', 'address', 'city', 'notes']
    list_filter = ['region', 'is_active', 'date_added']
    readonly_fields = ['date_added']
    raw_id_fields = ['contact_person']


class PlanSectionInline(admin.TabularInline):
    model = PlanSection
    extra = 0
    ordering = ['order']


@admin.register(BusinessPlan)
class BusinessPlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'owner', 'created_date', 'updated_date']
    search_fields = ['title', 'description']
    list_filter = ['status', 'created_date', 'updated_date']
    readonly_fields = ['created_date', 'updated_date']
    raw_id_fields = ['owner']
    inlines = [PlanSectionInline]


@admin.register(PlanSection)
class PlanSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'plan', 'order']
    search_fields = ['title', 'content']
    list_filter = ['plan']


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ['kpi_name', 'category', 'current_value', 'target_value', 'unit', 'last_updated']
    search_fields = ['kpi_name', 'description']
    list_filter = ['category', 'last_updated']
    readonly_fields = ['last_updated']
    raw_id_fields = ['updated_by']


@admin.register(KPIUpdateHistory)
class KPIUpdateHistoryAdmin(admin.ModelAdmin):
    list_display = ['kpi', 'previous_value', 'new_value', 'updated_by', 'updated_at']
    search_fields = ['notes']
    list_filter = ['updated_at']
    readonly_fields = ['updated_at']
    raw_id_fields = ['kpi', 'updated_by']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'priority', 'assigned_to', 'category', 'due_date', 'updated_date']
    search_fields = ['title', 'description']
    list_filter = ['status', 'priority', 'category', 'due_date', 'updated_date']
    readonly_fields = ['created_date', 'updated_date']
    raw_id_fields = ['assigned_to', 'created_by', 'related_site']


@admin.register(SocialMediaPost)
class SocialMediaPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'platform', 'status', 'scheduled_date', 'published_date', 'created_date']
    search_fields = ['title', 'content', 'hashtags', 'related_event']
    list_filter = ['platform', 'status', 'created_date', 'scheduled_date']
    readonly_fields = ['created_date', 'updated_date']
    raw_id_fields = ['created_by']
