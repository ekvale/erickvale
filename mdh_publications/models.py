import itertools

from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.template.defaultfilters import slugify

# Minnesota's most commonly supported community languages for MDH materials.
COMMUNITY_LANGUAGES = [
    ("en", "English"),
    ("es", "Spanish"),
    ("hmn", "Hmong"),
    ("so", "Somali"),
    ("ksw", "Karen"),
    ("vi", "Vietnamese"),
]

ACCEPTED_UPLOAD_EXTENSIONS = ["pdf", "docx", "xlsx", "csv", "pptx", "png", "jpg", "jpeg"]
DESCRIPTION_MIN_LENGTH = 150


class Facet(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class TopicGroup(models.Model):
    facet = models.ForeignKey(Facet, on_delete=models.CASCADE, related_name="topic_groups")
    slug = models.SlugField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["facet__sort_order", "name"]
        unique_together = ("facet", "slug")

    def __str__(self):
        return f"{self.facet.code} - {self.name}"


class Tag(models.Model):
    facet = models.ForeignKey(Facet, on_delete=models.CASCADE, related_name="tags")
    topic_group = models.ForeignKey(TopicGroup, on_delete=models.CASCADE, related_name="tags")
    slug = models.SlugField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    examples = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["facet__sort_order", "topic_group__name", "name"]

    def __str__(self):
        return self.name


class DocumentType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    scope_note = models.TextField(
        blank=True,
        help_text="Short controlled-vocabulary note describing when to use this type.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Publication(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_REVIEW = "in_review", "In Review"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(
        blank=True,
        help_text="Dublin Core description of the publication (minimum 150 characters on the upload form).",
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="publications",
    )
    publication_date = models.DateField(null=True, blank=True)
    language = models.CharField(
        max_length=8,
        choices=COMMUNITY_LANGUAGES,
        default="en",
        help_text="Language of this document, not the community it is about.",
    )
    is_translated = models.BooleanField(
        default=False,
        help_text="Check if this file is a translation of another publication.",
    )
    source_url = models.URLField(
        blank=True,
        help_text="Canonical public page for this publication (for example on health.mn.gov).",
    )
    file_upload = models.FileField(
        upload_to="mdh_publications/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=ACCEPTED_UPLOAD_EXTENSIONS)],
        help_text="Upload the document file. Accepted types: PDF, DOCX, XLSX, CSV, PPTX, PNG, JPG.",
    )
    pdf_text = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_featured = models.BooleanField(
        default=False,
        help_text="Only library stewards should feature publications on the landing page.",
    )
    facets = models.ManyToManyField(Facet, related_name="publications", blank=True)
    tags = models.ManyToManyField(Tag, related_name="publications", blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_publications",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_publications",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-publication_date", "title"]
        permissions = [
            ("publish_publication", "Can publish MDH publications"),
            ("manage_publication_taxonomy", "Can manage publication taxonomy"),
            ("manage_publication_roles", "Can manage publication roles"),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "publication"
            for index in itertools.count(1):
                candidate = base_slug if index == 1 else f"{base_slug}-{index}"
                if not Publication.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                    self.slug = candidate
                    break

        super().save(*args, **kwargs)


class LandingImage(models.Model):
    """
    Images for the Publications Library landing page, managed by administrators.

    The ``slot`` field controls where each image appears:
      - HERO              → rotating hero carousel at the top of the page
      - BROWSE_TOPIC      → "Browse by Topic" card image
      - BROWSE_CONTRIBUTOR→ "Browse by Contributor" card image
      - BROWSE_FORMAT     → "Browse by Format" card image

    For HERO, all active images rotate in sort_order sequence.
    For the three browse slots only the first active image (lowest sort_order) is used.
    """

    class Slot(models.TextChoices):
        HERO = "hero", "Hero Carousel"
        BROWSE_TOPIC = "browse_topic", "Browse by Topic Card"
        BROWSE_CONTRIBUTOR = "browse_contributor", "Browse by Contributor Card"
        BROWSE_FORMAT = "browse_format", "Browse by Format Card"

    slot = models.CharField(
        max_length=30,
        choices=Slot.choices,
        default=Slot.HERO,
        help_text="Where this image is displayed on the landing page.",
    )
    image = models.ImageField(upload_to="landing_images/")
    title = models.CharField(max_length=255)
    caption = models.TextField(blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="landing_images",
    )

    class Meta:
        ordering = ["slot", "sort_order", "-created_at"]

    def __str__(self):
        return f"[{self.get_slot_display()}] {self.title}"


class AccessRequest(models.Model):
    class RequestType(models.TextChoices):
        ACCESS = "access", "Request Access"
        SUGGESTION = "suggestion", "Suggest a Change"

    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    request_type = models.CharField(
        max_length=20,
        choices=RequestType.choices,
        default=RequestType.ACCESS,
    )
    reason = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.get_request_type_display()} from {self.name} ({self.submitted_at:%Y-%m-%d})"