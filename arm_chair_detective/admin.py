from django.contrib import admin
from .models import Suspect, Case, Clue, GameSession


@admin.register(Suspect)
class SuspectAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'gender', 'age_range', 'hair_color', 'vehicle_type', 'vehicle_color']
    list_filter = ['gender', 'age_range', 'hair_color', 'vehicle_type']
    search_fields = ['first_name', 'last_name', 'distinguishing_features']


class ClueInline(admin.TabularInline):
    model = Clue
    extra = 1


@admin.register(Case)
class CaseAdminWithClues(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'perpetrator', 'is_published', 'created_at']
    list_filter = ['difficulty', 'is_published']
    raw_id_fields = ['perpetrator']
    inlines = [ClueInline]


@admin.register(Clue)
class ClueAdmin(admin.ModelAdmin):
    list_display = ['title', 'case', 'clue_type', 'order', 'is_reliable']
    list_filter = ['clue_type', 'is_reliable']


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'case', 'started_at', 'completed_at', 'correct']
    list_filter = ['correct']
