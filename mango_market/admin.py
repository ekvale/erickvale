from django.contrib import admin
from .models import MarketSimulation


@admin.register(MarketSimulation)
class MarketSimulationAdmin(admin.ModelAdmin):
    list_display = ['name', 'season', 'region', 'created_at']
    list_filter = ['season', 'region', 'created_at']
    search_fields = ['name', 'season', 'region']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'season', 'region')
        }),
        ('Simulation Data', {
            'fields': ('simulation_data',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
