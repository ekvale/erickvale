from django.contrib import admin
from .models import HistoricalEvent, Collection, Tag, SiteStat


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
        'latitude',
        'longitude',
        'featured',
        'created_at',
    ]
    list_filter = ['featured', 'year', 'state', 'event_type']
    search_fields = ['title', 'summary', 'location']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['collections', 'tags']


@admin.register(SiteStat)
class SiteStatAdmin(admin.ModelAdmin):
    list_display = ['key', 'label', 'value', 'suffix']
