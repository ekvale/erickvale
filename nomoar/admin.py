from django.contrib import admin

from .models import (
    ChangeMaker,
    Collection,
    EventSource,
    HistoricalEvent,
    SiteStat,
    Tag,
)


class EventSourceInline(admin.TabularInline):
    model = EventSource
    extra = 0
    ordering = ['order', 'pk']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}


@admin.register(HistoricalEvent)
class HistoricalEventAdmin(admin.ModelAdmin):
    list_display = [
        'year',
        'title',
        'event_type',
        'location',
        'state',
        'last_reviewed',
        'latitude',
        'longitude',
        'featured',
        'created_at',
    ]
    list_filter = ['featured', 'year', 'state', 'event_type', 'last_reviewed']
    search_fields = ['title', 'summary', 'body', 'location']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['collections', 'tags']
    inlines = [EventSourceInline]
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'title',
                    'slug',
                    'year',
                    'event_type',
                    'summary',
                    'body',
                    'location',
                    'state',
                    'latitude',
                    'longitude',
                    'featured',
                    'raised_fists',
                    'collections',
                    'tags',
                )
            },
        ),
        (
            'Editorial',
            {
                'fields': ('last_reviewed', 'editorial_note'),
                'classes': ('collapse',),
            },
        ),
    )


@admin.register(EventSource)
class EventSourceAdmin(admin.ModelAdmin):
    list_display = ['citation', 'event', 'url', 'order']
    list_filter = ['event__year']
    search_fields = ['citation', 'url', 'event__title']


@admin.register(ChangeMaker)
class ChangeMakerAdmin(admin.ModelAdmin):
    list_display = ['name', 'tagline', 'order', 'is_published', 'updated_at']
    list_filter = ['is_published']
    search_fields = ['name', 'summary', 'tagline', 'body']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    filter_horizontal = ['related_events']


@admin.register(SiteStat)
class SiteStatAdmin(admin.ModelAdmin):
    list_display = ['key', 'label', 'value', 'suffix']
