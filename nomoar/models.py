"""
NOMOAR — National Online Museum of American Racism (inspired by nomoar.org).
A living archive of documented events, policies, and systems.
"""
from django.db import models
from django.urls import reverse


class ArchiveEventType(models.TextChoices):
    """Map marker / legend categories (aligned with nomoar.org-style archive)."""
    VIOLENCE = 'violence', 'Violence'
    POLICY = 'policy', 'Policy'
    LEGISLATION = 'legislation', 'Legislation'
    DISCRIMINATION = 'discrimination', 'Discrimination'


# Hex colors for Leaflet markers and UI (Violence=red, Policy=blue, Legislation=purple, Discrimination=orange)
ARCHIVE_EVENT_TYPE_COLORS = {
    ArchiveEventType.VIOLENCE: '#e53935',
    ArchiveEventType.POLICY: '#1e88e5',
    ArchiveEventType.LEGISLATION: '#8e24aa',
    ArchiveEventType.DISCRIMINATION: '#fb8c00',
}


class Tag(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Collection(models.Model):
    """Curated grouping of events."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class HistoricalEvent(models.Model):
    """Single documented entry in the archive."""
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    year = models.PositiveIntegerField(help_text='Primary year for sorting (e.g. 2025)')
    summary = models.TextField(help_text='Short description for cards and lists')
    body = models.TextField(blank=True, help_text='Optional longer narrative')
    location = models.CharField(max_length=300, blank=True)
    state = models.CharField(max_length=2, blank=True, help_text='US state code if applicable')
    event_type = models.CharField(
        max_length=32,
        choices=ArchiveEventType.choices,
        default=ArchiveEventType.POLICY,
        db_index=True,
        help_text='Category for map color and legend',
    )
    latitude = models.FloatField(
        null=True,
        blank=True,
        help_text='WGS84 latitude for map (e.g. 36.1)',
    )
    longitude = models.FloatField(
        null=True,
        blank=True,
        help_text='WGS84 longitude for map (e.g. -112.1)',
    )
    featured = models.BooleanField(default=False)
    raised_fists = models.PositiveIntegerField(default=0, help_text='Community acknowledgment count')
    collections = models.ManyToManyField(Collection, blank=True, related_name='events')
    tags = models.ManyToManyField(Tag, blank=True, related_name='events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', '-created_at']
        verbose_name = 'Historical event'
        verbose_name_plural = 'Historical events'
        indexes = [
            models.Index(fields=['-year', 'featured']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.year} — {self.title[:60]}"

    def get_absolute_url(self):
        return reverse('nomoar:event_detail', kwargs={'slug': self.slug})

    @property
    def event_type_color(self):
        return ARCHIVE_EVENT_TYPE_COLORS.get(self.event_type, '#1e88e5')


class SiteStat(models.Model):
    """Editable headline stats for the homepage."""
    key = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=50)
    suffix = models.CharField(max_length=20, blank=True, help_text='e.g. +')

    class Meta:
        ordering = ['key']

    def __str__(self):
        return f"{self.label}: {self.value}{self.suffix}"
