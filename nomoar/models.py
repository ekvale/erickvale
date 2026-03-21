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
    """Curated grouping of events (general, partner spotlight, or sponsored — disclose in sponsor fields)."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    partner_organization = models.CharField(
        max_length=200,
        blank=True,
        help_text='Library, museum, or org name for partner spotlight pages',
    )
    partner_url = models.URLField(blank=True, help_text='Partner website')
    guest_byline = models.CharField(
        max_length=300,
        blank=True,
        help_text='e.g. “Guest introduction by …”',
    )
    sponsor_disclosure = models.TextField(
        blank=True,
        help_text='Transparent note if a collection is underwritten (does not affect search ranking)',
    )
    is_partner_spotlight = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Highlight on educator / community pages',
    )
    is_published = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('nomoar:collection_detail', kwargs={'slug': self.slug})


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
    """Primary source: link, citation, optional file, context blurb, or media embed."""
    class SourceKind(models.TextChoices):
        LINK = 'link', 'Web link'
        DOCUMENT = 'document', 'Uploaded document'
        IMAGE = 'image', 'Image / scan'
        AUDIO_VIDEO = 'av', 'Audio / video embed'

    event = models.ForeignKey(
        HistoricalEvent,
        on_delete=models.CASCADE,
        related_name='sources',
    )
    source_kind = models.CharField(
        max_length=16,
        choices=SourceKind.choices,
        default=SourceKind.LINK,
    )
    url = models.URLField(max_length=500, blank=True)
    citation = models.CharField(
        max_length=500,
        blank=True,
        help_text='Publication, author, or short reference line',
    )
    context_note = models.TextField(
        blank=True,
        help_text='Short classroom-facing context for this source',
    )
    attachment = models.FileField(
        upload_to='nomoar/sources/',
        blank=True,
        null=True,
        help_text='PDF, image, or other file (optional)',
    )
    media_embed_url = models.URLField(
        max_length=500,
        blank=True,
        help_text='Link to audio/video or embeddable resource (oral history, etc.)',
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
    biography = models.TextField(
        blank=True,
        help_text='Full biography on the hero profile (below the summary)',
    )
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


class LearningPath(models.Model):
    """
    Curated guided sequence of archive entries (theme, place, decade, or tour).
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    intro = models.TextField(help_text='Introduction for classrooms / tours')
    theme_place_decade_note = models.CharField(
        max_length=300,
        blank=True,
        help_text='Optional subtitle (e.g. “Minnesota · 1960s · Policy”)',
    )
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True, db_index=True)
    show_on_start_here = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Featured on the “Start here” page (up to ~3 paths shown by order)',
    )
    start_here_order = models.PositiveIntegerField(
        default=0,
        help_text='Lower numbers appear first on Start here',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Learning path'
        verbose_name_plural = 'Learning paths'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('nomoar:learning_path_detail', kwargs={'slug': self.slug})


class LearningPathStep(models.Model):
    """One step in a learning path (ordered event + optional instructor note)."""
    path = models.ForeignKey(
        LearningPath,
        on_delete=models.CASCADE,
        related_name='steps',
    )
    event = models.ForeignKey(
        HistoricalEvent,
        on_delete=models.CASCADE,
        related_name='learning_path_steps',
    )
    order = models.PositiveIntegerField(default=0)
    instructor_note = models.TextField(
        blank=True,
        help_text='Discussion prompt or transition text before this entry',
    )

    class Meta:
        ordering = ['path', 'order', 'pk']
        verbose_name = 'Learning path step'
        verbose_name_plural = 'Learning path steps'
        constraints = [
            models.UniqueConstraint(
                fields=['path', 'event'],
                name='nomoar_learningpathstep_path_event_uniq',
            ),
        ]

    def __str__(self):
        return f'{self.path_id}:{self.order} → {self.event_id}'


class LessonKit(models.Model):
    """Lesson materials: standards, prompts, map/timeline activities, optional PDF."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    summary = models.TextField(blank=True)
    standards_alignment = models.TextField(
        blank=True,
        help_text='Standards or competencies this kit supports',
    )
    discussion_prompts = models.TextField(blank=True)
    map_timeline_activity = models.TextField(
        blank=True,
        help_text='Instructions using timeline, map, or embeddable widgets',
    )
    body = models.TextField(blank=True, help_text='Main lesson narrative / printable content')
    pdf_file = models.FileField(
        upload_to='nomoar/lesson_kits/',
        blank=True,
        null=True,
    )
    related_path = models.ForeignKey(
        LearningPath,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='lesson_kits',
    )
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Lesson kit'
        verbose_name_plural = 'Lesson kits'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('nomoar:lesson_kit_detail', kwargs={'slug': self.slug})


class NewsletterSubscriber(models.Model):
    """Educator / partner email list for “what’s new” digests (export from admin; connect mailer separately)."""
    email = models.EmailField(unique=True, db_index=True)
    active = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True, help_text='Internal')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Newsletter subscriber'
        verbose_name_plural = 'Newsletter subscribers'

    def __str__(self):
        return self.email


class GlossaryTerm(models.Model):
    """Stable URLs for key terms (syllabi, Wikipedia-style deep links)."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    definition = models.TextField()
    related_events = models.ManyToManyField(
        HistoricalEvent,
        blank=True,
        related_name='glossary_terms',
    )
    related_terms = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='related_from_terms',
        help_text='Cross-links to other glossary entries',
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Glossary term'
        verbose_name_plural = 'Glossary terms'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('nomoar:glossary_term_detail', kwargs={'slug': self.slug})


class ArchiveNewsPost(models.Model):
    """Short commentary connecting current events to archive entries (“in the news”)."""
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    teaser = models.TextField(blank=True)
    body = models.TextField()
    related_events = models.ManyToManyField(
        HistoricalEvent,
        blank=True,
        related_name='news_posts',
    )
    published_at = models.DateTimeField(db_index=True)
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-pk']
        verbose_name = 'Archive commentary post'
        verbose_name_plural = 'Archive commentary posts'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('nomoar:news_post_detail', kwargs={'slug': self.slug})


class LocalizedResourcePack(models.Model):
    """City / county slice + printable one-pager for local history groups."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    description = models.TextField(blank=True)
    city = models.CharField(max_length=120, blank=True)
    county = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=2, blank=True, help_text='US state code if applicable')
    embed_slice_hint = models.TextField(
        blank=True,
        help_text='Query string tips for /Embed/slice/?state=MN&decade=1960s etc.',
    )
    printable_pdf = models.FileField(
        upload_to='nomoar/packs/',
        blank=True,
        null=True,
    )
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Localized resource pack'
        verbose_name_plural = 'Localized resource packs'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('nomoar:resource_pack_detail', kwargs={'slug': self.slug})


class EngagementConfig(models.Model):
    """
    Singleton row (pk=1): donation, membership, institutional/API copy — edit in admin.
    """
    donation_url = models.URLField(blank=True, help_text='Donate / fundraiser link')
    membership_url = models.URLField(blank=True, help_text='Supporter or membership tiers')
    institutional_contact_email = models.EmailField(blank=True)
    api_partnerships_url = models.URLField(blank=True, help_text='API / data licensing info')
    grants_fiscal_sponsorship_blurb = models.TextField(
        blank=True,
        help_text='Shown on Support page',
    )
    museum_services_blurb = models.TextField(
        blank=True,
        help_text='Custom ingest, white-label map/timeline, consulting',
    )
    sponsorship_policy = models.TextField(
        blank=True,
        help_text='Transparent sponsored collections; no pay-for-placement in search',
    )
    things_to_avoid_note = models.TextField(
        blank=True,
        help_text='e.g. no programmatic ads on sensitive entries',
    )
    merch_print_blurb = models.TextField(blank=True, help_text='Posters, maps, print-on-demand')
    start_here_map_query = models.CharField(
        max_length=500,
        blank=True,
        help_text='Query string for the “Start here” map link, e.g. year_from=2020&year_to=2026&type=policy',
    )

    class Meta:
        verbose_name = 'Engagement & support settings'
        verbose_name_plural = 'Engagement & support settings'

    def __str__(self):
        return 'Engagement & support settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


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
