from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import json


class POD(models.Model):
    """Point of Distribution model for emergency preparedness planning."""
    
    STATUS_CHOICES = [
        ('proposed', 'Proposed'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    coverage_radius = models.FloatField(default=50.0)  # in kilometers
    occupancy = models.IntegerField(default=0)  # capacity
    parking_lot_size = models.FloatField(default=0.0)  # in acres
    acreage = models.FloatField(default=0.0)  # total acreage
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposed')
    points_covered = models.IntegerField(default=0)  # calculated field
    total_risk_covered = models.FloatField(default=0.0)  # calculated field
    total_population_covered = models.IntegerField(default=0)  # calculated field
    avg_drive_time = models.FloatField(default=0.0)  # in minutes
    max_drive_time = models.FloatField(default=0.0)  # in minutes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'POD'
        verbose_name_plural = 'PODs'
    
    def clean(self):
        """Validate coordinates are within Minnesota bounds."""
        from .utils import constrain_to_minnesota
        
        lat = float(self.latitude)
        lon = float(self.longitude)
        
        constrained_lat, constrained_lon = constrain_to_minnesota(lat, lon)
        
        # Round to 6 decimal places and convert to Decimal
        constrained_lat = round(constrained_lat, 6)
        constrained_lon = round(constrained_lon, 6)
        
        if lat != constrained_lat or lon != constrained_lon:
            self.latitude = Decimal(str(constrained_lat))
            self.longitude = Decimal(str(constrained_lon))
    
    def save(self, *args, **kwargs):
        """Override save to ensure coordinates are constrained."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Scenario(models.Model):
    """Emergency scenario model for planning different disaster types."""
    
    TYPE_CHOICES = [
        ('general', 'General'),
        ('pandemic', 'Pandemic'),
        ('natural_disaster', 'Natural Disaster'),
        ('severe_weather', 'Severe Weather'),
        ('infrastructure_failure', 'Infrastructure Failure'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='general')
    severity = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.5), MaxValueValidator(3.0)]
    )
    affected_areas = models.JSONField(default=list, blank=True)  # List of area names or coordinates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    pods = models.ManyToManyField(POD, through='ScenarioPOD', related_name='scenarios')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ScenarioPOD(models.Model):
    """Many-to-many relationship between Scenario and POD."""
    
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    pod = models.ForeignKey(POD, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['scenario', 'pod']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.scenario.name} - {self.pod.name}"
