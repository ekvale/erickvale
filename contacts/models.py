from django.db import models


class ContactSource(models.TextChoices):
    GMAIL = 'gmail', 'Gmail'
    LINKEDIN = 'linkedin', 'LinkedIn'
    FACEBOOK = 'facebook', 'Facebook'
    PHONE = 'phone', 'Phone / vCard'
    MANUAL = 'manual', 'Manual'


class Contact(models.Model):
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    display_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Fallback if no first/last name',
    )
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=50, blank=True)
    birthday = models.DateField(null=True, blank=True)
    company = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)

    source = models.CharField(
        max_length=20,
        choices=ContactSource.choices,
        default=ContactSource.MANUAL,
        db_index=True,
    )
    source_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='External ID for deduplication',
    )

    projects = models.ManyToManyField(
        'projects.Project',
        blank=True,
        related_name='contacts',
    )
    tasks = models.ManyToManyField(
        'projects.Task',
        blank=True,
        related_name='contacts',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name', 'display_name']
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'source_id'],
                condition=~models.Q(source_id=''),
                name='contacts_unique_source_id',
            ),
        ]

    def __str__(self):
        label = self.display_name or f'{self.first_name} {self.last_name}'.strip()
        return label or self.email or f'Contact #{self.pk}'
