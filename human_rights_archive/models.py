"""
Human Rights & Constitutional Violations Archive models.
"""
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Source(models.Model):
    """RSS/Atom feed or other source for articles."""
    SOURCE_TYPE_CHOICES = [
        ('rss', 'RSS'),
        ('atom', 'Atom'),
        ('other', 'Other'),
    ]

    url = models.URLField(max_length=500)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES, default='rss')
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    last_fetched = models.DateTimeField(null=True, blank=True)
    last_fetch_status = models.CharField(max_length=50, blank=True)  # success, error, etc.
    last_fetch_message = models.TextField(blank=True)
    fetch_interval_hours = models.PositiveIntegerField(default=24, help_text='Hours between fetches')
    default_tags = models.ManyToManyField('Tag', related_name='sources_with_default', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Source'
        verbose_name_plural = 'Sources'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tag for classifying articles (human rights, constitutional, etc.)."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=50, blank=True,
        help_text='e.g. human rights, constitutional, civil liberties'
    )

    class Meta:
        ordering = ['category', 'name']
        indexes = [models.Index(fields=['slug'])]

    def __str__(self):
        return self.name


class Article(models.Model):
    """Article/record from a source (RSS item or scraped page)."""
    title = models.CharField(max_length=500, db_index=True)
    url = models.URLField(max_length=2000, unique=True, db_index=True)
    summary = models.TextField(blank=True)
    content = models.TextField(blank=True, help_text='Full text when stored')
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    fetched_at = models.DateTimeField(auto_now_add=True)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    tags = models.ManyToManyField(Tag, related_name='articles', blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='archived_articles'
    )

    class Meta:
        ordering = ['-published_at', '-fetched_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['source', '-published_at']),
        ]

    def __str__(self):
        return self.title[:80] + ('…' if len(self.title) > 80 else '')

    def get_absolute_url(self):
        return reverse('human_rights_archive:article_detail', kwargs={'pk': self.pk})


class FeedFetchLog(models.Model):
    """Log of feed fetch runs for auditing."""
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='fetch_logs')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20)  # success, error, partial
    articles_added = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.source.name} @ {self.started_at} - {self.status}"
