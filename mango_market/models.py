from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
import json


class MarketSimulation(models.Model):
    """Stores market simulation results with historical tracking."""
    name = models.CharField(max_length=200, default="Tanzania Mango Market Simulation", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    simulation_data = models.JSONField(default=dict, help_text="Complete simulation results")
    
    # Key parameters used for this simulation
    quantity_kg = models.IntegerField(default=1000, validators=[MinValueValidator(1)], help_text="Quantity in kg")
    simulation_days = models.IntegerField(default=30, validators=[MinValueValidator(1)], help_text="Number of days simulated")
    season = models.CharField(max_length=50, default="Peak Season")
    region = models.CharField(max_length=100, default="Tanzania")
    
    # Summary metrics for quick access
    fresh_net_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    dried_net_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    hybrid_net_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    best_strategy = models.CharField(max_length=20, blank=True, help_text="Fresh, Dried, or Hybrid")
    avg_fresh_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    avg_dried_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Metadata
    is_saved = models.BooleanField(default=True, help_text="Whether this simulation should be kept for historical reference")
    notes = models.TextField(blank=True, help_text="Optional notes about this simulation")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Market Simulation'
        verbose_name_plural = 'Market Simulations'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['season', 'region']),
        ]
    
    def __str__(self):
        date_str = self.created_at.strftime('%Y-%m-%d %H:%M')
        return f"{self.region} - {self.quantity_kg}kg - {date_str}"
    
    def get_fresh_vs_dried_profitability(self):
        """Returns profitability comparison data."""
        return self.simulation_data.get('profitability_comparison', {})
    
    def get_price_trends(self):
        """Returns price trend data."""
        return self.simulation_data.get('price_trends', {})
    
    def get_market_analysis(self):
        """Returns market analysis summary."""
        return self.simulation_data.get('market_analysis', {})
    
