from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.urls import reverse


class ActivityTag(models.Model):
    """Tag for categorizing activities in media uploads."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Activity Tag'
        verbose_name_plural = 'Activity Tags'
    
    def __str__(self):
        return self.name


class MediaItem(models.Model):
    """Model for uploaded videos and photos with activity tags and location."""
    
    MEDIA_TYPE_CHOICES = [
        ('photo', 'Photo'),
        ('video', 'Video'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_items')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    file = models.FileField(
        upload_to='activity_media/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'avi', 'mkv']
            )
        ]
    )
    thumbnail = models.ImageField(
        upload_to='activity_media/thumbnails/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text='Auto-generated for videos, optional for photos'
    )
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    # Location fields
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_name = models.CharField(max_length=200, blank=True, help_text='Optional location name/address')
    
    # Activity tags
    activity_tags = models.ManyToManyField(ActivityTag, related_name='media_items', blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True, help_text='Whether this media is visible to all users')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Media Item'
        verbose_name_plural = 'Media Items'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['media_type']),
            models.Index(fields=['latitude', 'longitude']),
        ]
        permissions = [
            ('can_upload_media', 'Can upload media'),
        ]
    
    def __str__(self):
        return f"{self.media_type.title()} - {self.title or self.file.name} by {self.user.username}"
    
    def get_absolute_url(self):
        return reverse('activity_media:detail', kwargs={'pk': self.pk})
    
    def has_location(self):
        """Check if media item has location data."""
        return self.latitude is not None and self.longitude is not None
