from django.db import models
from django.utils import timezone
import json


class MarketSimulation(models.Model):
    """Stores market simulation results."""
    name = models.CharField(max_length=200, default="Tanzania Mango Market Simulation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    simulation_data = models.JSONField(default=dict, help_text="Complete simulation results")
    
    # Key parameters
    season = models.CharField(max_length=50, default="Peak Season")
    region = models.CharField(max_length=100, default="Tanzania")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Market Simulation'
        verbose_name_plural = 'Market Simulations'
    
    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_fresh_vs_dried_profitability(self):
        """Returns profitability comparison data."""
        return self.simulation_data.get('profitability_comparison', {})
    
    def get_price_trends(self):
        """Returns price trend data."""
        return self.simulation_data.get('price_trends', {})
    
    def get_market_analysis(self):
        """Returns market analysis summary."""
        return self.simulation_data.get('market_analysis', {})
