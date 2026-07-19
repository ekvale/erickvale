from django.contrib import admin

from .models import HighScore


@admin.register(HighScore)
class HighScoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'score', 'era_reached', 'waves_cleared', 'victory', 'created_at')
    list_filter = ('victory',)
    search_fields = ('name',)
    ordering = ('-score',)
