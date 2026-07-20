from django.db import models
from django.urls import reverse


class FeaturedApp(models.Model):
    """A project in the personal portfolio showcase (erickvale.com homepage / work page)."""

    CATEGORY_CHOICES = [
        ('data', 'Data & Analytics'),
        ('games', 'Games & Play'),
        ('tools', 'Tools & Utilities'),
        ('research', 'Writing & Research'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, help_text="URL-friendly version of the name")
    tagline = models.CharField(max_length=140, blank=True, default='', help_text="Short one-line hook shown on the project tile")
    description = models.TextField(help_text="Description shown on the homepage")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='tools')
    icon = models.CharField(max_length=10, default='📱', help_text="Emoji icon")
    url = models.CharField(max_length=200, help_text="URL path to the app (e.g., /apps/cards/)")
    featured_size = models.CharField(
        max_length=10,
        choices=[('large', 'Large tile'), ('normal', 'Normal tile')],
        default='normal',
        help_text="Large tiles get a bigger spot in the bento grid. Reserve for flagship projects.",
    )
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
        return f"{self.name} - {status}"

    def get_absolute_url(self):
        return self.url

