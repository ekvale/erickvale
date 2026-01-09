from django.contrib import admin
from .models import Scenario, GameSession, GameRound


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ['id', 'scenario_title', 'difficulty', 'correct_type', 'tell_category', 'is_feels_unheard']
    list_filter = ['difficulty', 'correct_type', 'tell_category', 'is_feels_unheard']
    search_fields = ['scenario_title', 'tell_explanation', 'response_explanation']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('scenario_title', 'difficulty', 'is_feels_unheard')
        }),
        ('Content', {
            'fields': ('transcript',)
        }),
        ('Correct Answers', {
            'fields': ('correct_type', 'tell_category', 'tell_explanation')
        }),
        ('Responses', {
            'fields': ('response_choices', 'correct_response', 'response_explanation')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'difficulty', 'training_mode', 'total_score', 'total_rounds', 'best_streak', 'started_at', 'completed']
    list_filter = ['difficulty', 'training_mode', 'completed']
    search_fields = ['session_id']
    readonly_fields = ['session_id', 'started_at', 'last_activity', 'get_accuracy']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Session Info', {
            'fields': ('session_id', 'difficulty', 'training_mode', 'completed')
        }),
        ('Statistics', {
            'fields': ('total_score', 'total_rounds', 'current_streak', 'best_streak', 'get_accuracy')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'last_activity')
        }),
    )
    
    def get_accuracy(self, obj):
        return f"{obj.get_accuracy()}%"
    get_accuracy.short_description = 'Accuracy'


@admin.register(GameRound)
class GameRoundAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'round_number', 'scenario', 'player_type_guess', 'type_correct', 'response_correct', 'points_earned', 'hint_used']
    list_filter = ['type_correct', 'response_correct', 'tell_correct', 'hint_used']
    search_fields = ['session__session_id', 'scenario__scenario_title']
    readonly_fields = ['answered_at']
    raw_id_fields = ['session', 'scenario']
