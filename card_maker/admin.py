from django.contrib import admin
from django.utils.html import format_html
from .models import CardSet, Card


@admin.register(CardSet)
class CardSetAdmin(admin.ModelAdmin):
    list_display = ['thumbnail', 'name', 'slug', 'is_active', 'created_at', 'card_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'thumbnail_preview']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'is_active')
        }),
        ('Visual', {
            'fields': ('cover_image', 'thumbnail_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def card_count(self, obj):
        return obj.cards.count()
    card_count.short_description = 'Cards'
    
    def thumbnail(self, obj):
        """Display thumbnail image in list view."""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.cover_image.url
            )
        else:
            return format_html(
                '<div style="width: 50px; height: 50px; background: #2a2a2a; border: 1px solid #444; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 24px;">📚</div>'
            )
    thumbnail.short_description = 'Cover'
    
    def thumbnail_preview(self, obj):
        """Display larger thumbnail in detail view."""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; object-fit: contain; border: 1px solid #444; border-radius: 4px; padding: 8px; background: #1a1a1a;" />',
                obj.cover_image.url
            )
        else:
            return format_html(
                '<div style="width: 200px; height: 200px; background: #2a2a2a; border: 1px solid #444; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 80px;">📚</div>'
            )
    thumbnail_preview.short_description = 'Cover Preview'


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['thumbnail', 'name', 'card_set', 'card_type', 'rarity', 'level', 'stat_summary_display', 'is_active']
    list_filter = ['card_set', 'card_type', 'rarity', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'abilities']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'total_stats', 'thumbnail_preview']
    actions = ['regenerate_kvale_cards']
    
    def regenerate_kvale_cards(self, request, queryset):
        """Admin action to regenerate Kvale card images."""
        count = 0
        for card in queryset:
            if card.card_set.slug == 'kvale':
                if card.generate_kvale_card_image():
                    card.save(update_fields=['card_image'])
                    count += 1
        self.message_user(request, f'Successfully regenerated {count} card image(s).')
    regenerate_kvale_cards.short_description = 'Regenerate Kvale card images'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'card_set', 'card_type', 'rarity', 'order', 'is_active')
        }),
        ('Visual', {
            'fields': ('card_image', 'card_image_alt', 'thumbnail_preview')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Dungeon Crawler Carl Stats', {
            'fields': (
                'level',
                ('strength', 'intelligence', 'constitution'),
                ('dexterity', 'charisma'),
            ),
            'description': 'DCC stat system: STR, INT, CON, DEX, CHR'
        }),
        ('Kvale Card Stats', {
            'fields': (
                ('energy', 'power'),
                ('trigger', 'album_label'),
                ('tags',),
                ('edition', 'collection'),
            ),
            'description': 'Stats for Kvale printable card format',
            'classes': ('collapse',)
        }),
        ('Additional Stats', {
            'fields': ('additional_stats',),
            'classes': ('collapse',)
        }),
        ('Abilities', {
            'fields': ('abilities',)
        }),
        ('Metadata', {
            'fields': ('total_stats', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def stat_summary_display(self, obj):
        return obj.stat_summary or 'No stats'
    stat_summary_display.short_description = 'Stats'
    
    def thumbnail(self, obj):
        """Display thumbnail image in list view."""
        if obj.card_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.card_image.url
            )
        else:
            return format_html(
                '<div style="width: 50px; height: 50px; background: #2a2a2a; border: 1px solid #444; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 24px;">🃏</div>'
            )
    thumbnail.short_description = 'Image'
    
    def thumbnail_preview(self, obj):
        """Display larger thumbnail in detail view."""
        if obj.card_image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; object-fit: contain; border: 1px solid #444; border-radius: 4px; padding: 8px; background: #1a1a1a;" />',
                obj.card_image.url
            )
        else:
            return format_html(
                '<div style="width: 200px; height: 200px; background: #2a2a2a; border: 1px solid #444; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 80px;">🃏</div>'
            )
    thumbnail_preview.short_description = 'Image Preview'
