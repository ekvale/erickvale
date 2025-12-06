from django.db import models
from django.urls import reverse


class FeaturedApp(models.Model):
    """Model for featured monthly applications."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, help_text="URL-friendly version of the name")
    description = models.TextField(help_text="Description shown on the homepage")
    icon = models.CharField(max_length=10, default='📱', help_text="Emoji icon")
    url = models.CharField(max_length=200, help_text="URL path to the app (e.g., /apps/cards/)")
    cover_image = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Path to cover image (e.g., erickvale/images/king_and_death.avif)"
    )
    features = models.JSONField(
        default=list,
        blank=True,
        help_text="List of features (e.g., ['Feature 1', 'Feature 2'])"
    )
    month = models.CharField(max_length=50, help_text="Month/year (e.g., 'January 2025')")
    is_current_month = models.BooleanField(
        default=False,
        help_text="Is this the current month's featured app?"
    )
    is_published = models.BooleanField(
        default=True,
        help_text="Show this app on the homepage"
    )
    order = models.IntegerField(
        default=0,
        help_text="Order for display (lower numbers appear first)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Featured App'
        verbose_name_plural = 'Featured Apps'

    def __str__(self):
        status = "Published" if self.is_published else "Unpublished"
        current = " (Current)" if self.is_current_month else ""
        return f"{self.name} - {status}{current}"

    def get_absolute_url(self):
        return self.url

