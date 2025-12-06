from django.contrib import admin
from .models import FeaturedApp


@admin.register(FeaturedApp)
class FeaturedAppAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'month', 'is_current_month', 'is_published', 'order', 'created_at']
    list_filter = ['is_published', 'is_current_month', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'icon', 'url', 'month')
        }),
        ('Visual', {
            'fields': ('cover_image',)
        }),
        ('Features', {
            'fields': ('features',),
            'description': 'Enter features as a JSON array, e.g., ["Feature 1", "Feature 2"]'
        }),
        ('Display Settings', {
            'fields': ('is_current_month', 'is_published', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

