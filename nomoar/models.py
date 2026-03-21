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


class EventThemeLabel(models.Model):
    """
    Top-row pills on timeline cards (e.g. institutional, cultural, court case).
    Distinct from ArchiveEventType (violence/policy/…) and from Tag (affected groups).
    """
    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=120, help_text='Shown on cards (lowercased in CSS)')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'slug']
        verbose_name = 'Theme label'
        verbose_name_plural = 'Theme labels'

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
    theme_labels = models.ManyToManyField(
        EventThemeLabel,
        blank=True,
        related_name='events',
        help_text='Pills above the title (institutional, cultural, court case, …)',
    )
    curated_related = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='related_from_curated',
        help_text='Manually curated related entries (shown first on the detail page).',
    )
    last_reviewed = models.DateField(
        null=True,
        blank=True,
        help_text='Last editorial or fact-check review (optional)',
    )
    editorial_note = models.TextField(
        blank=True,
        help_text='Optional note shown on the entry (e.g. review status)',
    )
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

    @property
    def is_geocoded(self):
        return self.latitude is not None and self.longitude is not None


class EventFistVote(models.Model):
    """One raised-fist per browser session per event (toggle on/off)."""
    event = models.ForeignKey(
        HistoricalEvent,
        on_delete=models.CASCADE,
        related_name='fist_votes',
    )
    session_key = models.CharField(max_length=40, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'session_key'],
                name='nomoar_eventfistvote_event_session_uniq',
            ),
        ]

    def __str__(self):
        return f'{self.event_id}:{self.session_key[:8]}…'


class EventSource(models.Model):
    """URL + short citation for a historical event (admin inline)."""
    event = models.ForeignKey(
        HistoricalEvent,
        on_delete=models.CASCADE,
        related_name='sources',
    )
    url = models.URLField(max_length=500, blank=True)
    citation = models.CharField(
        max_length=500,
        blank=True,
        help_text='Publication, author, or short reference line',
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'Source'
        verbose_name_plural = 'Sources'

    def __str__(self):
        return self.citation[:60]


class ChangeMaker(models.Model):
    """
    People who resisted racism and advanced justice — companion to the events archive.
    Editable in admin; seeded from fixtures for local/demo use.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    tagline = models.CharField(
        max_length=300,
        blank=True,
        help_text='Short role or descriptor under the name',
    )
    summary = models.TextField(help_text='Card text on the Heroes index')
    body = models.TextField(blank=True, help_text='Longer biography on the detail page')
    birth_year = models.PositiveIntegerField(null=True, blank=True)
    death_year = models.PositiveIntegerField(null=True, blank=True)
    portrait = models.ImageField(
        upload_to='nomoar/heroes/',
        blank=True,
        null=True,
        help_text='Optional photo (upload in admin)',
    )
    related_events = models.ManyToManyField(
        HistoricalEvent,
        blank=True,
        related_name='related_heroes',
        help_text='Timeline entries to highlight on this profile',
    )
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Change maker / hero'
        verbose_name_plural = 'Change makers & heroes'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('nomoar:hero_detail', kwargs={'slug': self.slug})

    @property
    def life_span_display(self):
        if self.birth_year and self.death_year:
            return f'{self.birth_year}–{self.death_year}'
        if self.birth_year:
            return f'b. {self.birth_year}'
        return ''

    @property
    def initials(self):
        parts = self.name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return (self.name[:2] if self.name else '?').upper()


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
