from django.contrib import admin
from .models import FeaturedApp


@admin.register(FeaturedApp)
class FeaturedAppAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'featured_size', 'is_published', 'order', 'updated_at']
    list_filter = ['category', 'featured_size', 'is_published']
    search_fields = ['name', 'slug', 'description', 'tagline']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['order', 'is_published']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'tagline', 'description', 'category', 'icon', 'url')
        }),
        ('Visual', {
            'fields': ('cover_image', 'featured_size')
        }),
        ('Features', {
            'fields': ('features',),
            'description': 'Enter features as a JSON array, e.g., ["Feature 1", "Feature 2"]'
        }),
        ('Display Settings', {
            'fields': ('is_published', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
