from django.contrib import admin
from .models import MediaItem, ActivityTag


@admin.register(ActivityTag)
class ActivityTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']
    
    class Meta:
        verbose_name = 'Activity Tag'
        verbose_name_plural = 'Activity Tags'


@admin.register(MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'media_type', 'has_location', 'created_at', 'is_public']
    list_filter = ['media_type', 'is_public', 'created_at', 'activity_tags']
    search_fields = ['title', 'description', 'location_name', 'user__username']
    filter_horizontal = ['activity_tags']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Media Information', {
            'fields': ('user', 'media_type', 'file', 'thumbnail', 'title', 'description')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude', 'location_name')
        }),
        ('Activity Tags', {
            'fields': ('activity_tags',)
        }),
        ('Settings', {
            'fields': ('is_public',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('activity_tags')
