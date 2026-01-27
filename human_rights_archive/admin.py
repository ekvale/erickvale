from django.contrib import admin
from .models import Source, Tag, Article, FeedFetchLog


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'url', 'is_active', 'last_fetched', 'last_fetch_status']
    list_filter = ['source_type', 'is_active']
    search_fields = ['name', 'url']
    filter_horizontal = ['default_tags']
    readonly_fields = ['last_fetched', 'last_fetch_status', 'last_fetch_message', 'created_at', 'updated_at']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'has_keywords']
    list_filter = ['category']
    search_fields = ['name', 'slug', 'description', 'keywords']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'description'),
        }),
        ('Auto-tagging keywords', {
            'fields': ('keywords',),
            'description': 'Comma-separated keywords. When an article’s title, summary, or content contains any of these (case-insensitive), this tag is applied during fetch or “Add by URL”. Leave blank to disable auto-tagging for this tag.',
        }),
    )

    def has_keywords(self, obj):
        return bool(obj.keywords)
    has_keywords.boolean = True


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'published_at', 'fetched_at']
    list_filter = ['source', 'published_at']
    search_fields = ['title', 'summary', 'content', 'url']
    filter_horizontal = ['tags']
    readonly_fields = ['fetched_at']
    date_hierarchy = 'published_at'


@admin.register(FeedFetchLog)
class FeedFetchLogAdmin(admin.ModelAdmin):
    list_display = ['source', 'started_at', 'status', 'articles_added']
    list_filter = ['status', 'source']
    readonly_fields = ['started_at', 'completed_at']
