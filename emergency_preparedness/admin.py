from django.contrib import admin
from .models import POD, Scenario, ScenarioPOD


@admin.register(POD)
class PODAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'latitude', 'longitude', 'coverage_radius',
                   'points_covered', 'total_population_covered', 'max_drive_time', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'points_covered', 'total_risk_covered',
                      'total_population_covered', 'avg_drive_time', 'max_drive_time')


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'severity', 'created_at')
    list_filter = ('type', 'severity', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ScenarioPOD)
class ScenarioPODAdmin(admin.ModelAdmin):
    list_display = ('scenario', 'pod', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('scenario__name', 'pod__name')
    readonly_fields = ('created_at',)
