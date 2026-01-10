from django.contrib import admin
from .models import MarketSimulation


@admin.register(MarketSimulation)
class MarketSimulationAdmin(admin.ModelAdmin):
    list_display = ['id', 'region', 'quantity_kg', 'simulation_days', 'best_strategy', 'fresh_net_revenue', 'dried_net_revenue', 'is_saved', 'created_at']
    list_filter = ['season', 'region', 'best_strategy', 'is_saved', 'created_at']
    search_fields = ['region', 'season', 'best_strategy', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_saved']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'season', 'region', 'quantity_kg', 'simulation_days')
        }),
        ('Summary Metrics', {
            'fields': ('best_strategy', 'fresh_net_revenue', 'dried_net_revenue', 'hybrid_net_revenue', 
                      'avg_fresh_price', 'avg_dried_price')
        }),
        ('Simulation Data', {
            'fields': ('simulation_data',),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('is_saved', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
