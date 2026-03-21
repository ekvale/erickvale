from django.contrib import admin

from .models import (
    ArchiveNewsPost,
    ChangeMaker,
    Collection,
    EngagementConfig,
    EventSource,
    EventThemeLabel,
    GlossaryTerm,
    HistoricalEvent,
    LearningPath,
    LearningPathStep,
    LessonKit,
    LocalizedResourcePack,
    NewsletterSubscriber,
    SiteStat,
    Tag,
)


class EventSourceInline(admin.TabularInline):
    model = EventSource
    extra = 0
    ordering = ['order', 'pk']
    fields = [
        'order',
        'source_kind',
        'citation',
        'url',
        'context_note',
        'attachment',
        'media_embed_url',
    ]


class LearningPathStepInline(admin.TabularInline):
    model = LearningPathStep
    extra = 0
    ordering = ['order', 'pk']
    autocomplete_fields = ['event']
    fields = ['order', 'event', 'instructor_note']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(EventThemeLabel)
class EventThemeLabelAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'slug']


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'is_published',
        'is_partner_spotlight',
        'partner_organization',
        'order',
    ]
    list_filter = ['is_published', 'is_partner_spotlight']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'description', 'partner_organization', 'guest_byline']
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'description', 'order', 'is_published')}),
        (
            'Partner / sponsor (transparent)',
            {
                'fields': (
                    'is_partner_spotlight',
                    'partner_organization',
                    'partner_url',
                    'guest_byline',
                    'sponsor_disclosure',
                ),
            },
        ),
    )


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
    filter_horizontal = ['collections', 'tags', 'theme_labels', 'curated_related']
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
                    'theme_labels',
                    'curated_related',
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
    list_display = ['citation', 'event', 'source_kind', 'url', 'order']
    list_filter = ['source_kind', 'event__year']
    search_fields = ['citation', 'url', 'event__title', 'context_note']


@admin.register(ChangeMaker)
class ChangeMakerAdmin(admin.ModelAdmin):
    list_display = ['name', 'tagline', 'order', 'is_published', 'updated_at']
    list_filter = ['is_published']
    search_fields = ['name', 'summary', 'tagline', 'biography']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    filter_horizontal = ['related_events']
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'tagline', 'summary', 'biography')}),
        ('Meta', {'fields': ('birth_year', 'death_year', 'portrait', 'related_events', 'order', 'is_published')}),
    )


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_published', 'order', 'updated_at']
    list_filter = ['is_published']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'intro', 'theme_place_decade_note']
    inlines = [LearningPathStepInline]


@admin.register(LessonKit)
class LessonKitAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_published', 'related_path', 'order']
    list_filter = ['is_published']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'summary', 'body']
    autocomplete_fields = ['related_path']


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'active', 'created_at', 'notes']
    list_filter = ['active']
    search_fields = ['email']


@admin.register(GlossaryTerm)
class GlossaryTermAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'order']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'definition']
    filter_horizontal = ['related_events']


@admin.register(ArchiveNewsPost)
class ArchiveNewsPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'published_at', 'is_published']
    list_filter = ['is_published']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'teaser', 'body']
    filter_horizontal = ['related_events']
    date_hierarchy = 'published_at'


@admin.register(LocalizedResourcePack)
class LocalizedResourcePackAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'city', 'county', 'state', 'is_published', 'order']
    list_filter = ['is_published', 'state']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'description', 'city', 'county']


@admin.register(EngagementConfig)
class EngagementConfigAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not EngagementConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiteStat)
class SiteStatAdmin(admin.ModelAdmin):
    list_display = ['key', 'label', 'value', 'suffix']
