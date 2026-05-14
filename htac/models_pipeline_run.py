"""
Pipeline demonstration run tracking (HTAC narrative demo).

Kept in a separate module and re-exported from htac.models for Django discovery.
"""

from __future__ import annotations

from django.db import models


class PipelineRun(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("complete", "Complete"),
        ("failed", "Failed"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    total_patients_raw = models.IntegerField(default=0)
    total_patients_deduplicated = models.IntegerField(default=0)
    cross_site_matches = models.IntegerField(default=0)
    homeless_flagged = models.IntegerField(default=0)
    incarcerated_flagged = models.IntegerField(default=0)
    medicaid_flagged = models.IntegerField(default=0)
    total_estimates_generated = models.IntegerField(default=0)
    total_estimates_suppressed = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "htac"
        ordering = ["-created_at"]

    def __str__(self):
        return f"PipelineRun {self.pk} ({self.status})"


class PipelineStep(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("complete", "Complete"),
        ("failed", "Failed"),
    ]

    run = models.ForeignKey(
        PipelineRun, on_delete=models.CASCADE, related_name="steps"
    )
    step_number = models.IntegerField()
    step_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    narrative_headline = models.CharField(max_length=200, blank=True)
    narrative_body = models.TextField(blank=True)
    technical_detail = models.TextField(blank=True)
    metric_label = models.CharField(max_length=100, blank=True)
    metric_value = models.CharField(max_length=100, blank=True)
    site_data = models.JSONField(default=dict)

    class Meta:
        app_label = "htac"
        ordering = ["step_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["run", "step_number"],
                name="htac_pipelinestep_unique_run_step_number",
            ),
        ]

    def __str__(self):
        return f"Step {self.step_number} ({self.status})"
