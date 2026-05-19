from django.contrib import admin

from .models import LeaderBriefing


@admin.register(LeaderBriefing)
class LeaderBriefingAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'date', 'leader_id', 'generated_at')
    list_filter = ('date', 'bureau')
    search_fields = ('name', 'leader_id', 'title')
    readonly_fields = ('generated_at',)
