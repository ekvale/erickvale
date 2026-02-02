"""
Models for All Minnesota operations and project management dashboard.
Indigenous-led community meal distribution and fundraising program.
"""
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal


# --- Contact type choices ---
class ContactType(models.TextChoices):
    VOLUNTEER = 'VOLUNTEER', 'Volunteer'
    DONOR = 'DONOR', 'Donor'
    TRIBAL_PARTNER = 'TRIBAL_PARTNER', 'Tribal Partner'
    MEDIA = 'MEDIA', 'Media'
    COMMUNITY_MEMBER = 'COMMUNITY_MEMBER', 'Community Member'
    ORGANIZATION = 'ORGANIZATION', 'Organization'


# --- Region choices for distribution sites ---
class Region(models.TextChoices):
    TWIN_CITIES = 'TWIN_CITIES', 'Twin Cities'
    GREATER_MINNESOTA = 'GREATER_MINNESOTA', 'Greater Minnesota'


# --- Business plan status ---
class PlanStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    ACTIVE = 'ACTIVE', 'Active'
    ARCHIVED = 'ARCHIVED', 'Archived'


# --- KPI category ---
class KPICategory(models.TextChoices):
    FUNDRAISING = 'FUNDRAISING', 'Fundraising'
    MEALS_DELIVERED = 'MEALS_DELIVERED', 'Meals Delivered'
    VOLUNTEERS = 'VOLUNTEERS', 'Volunteers'
    DISTRIBUTION = 'DISTRIBUTION', 'Distribution'
    OUTREACH = 'OUTREACH', 'Outreach'


# --- Task priority and status ---
class TaskPriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    URGENT = 'URGENT', 'Urgent'


class TaskStatus(models.TextChoices):
    TODO = 'TODO', 'To Do'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    ON_HOLD = 'ON_HOLD', 'On Hold'


class TaskCategory(models.TextChoices):
    FUNDRAISING = 'FUNDRAISING', 'Fundraising'
    LOGISTICS = 'LOGISTICS', 'Logistics'
    SOCIAL_MEDIA = 'SOCIAL_MEDIA', 'Social Media'
    OUTREACH = 'OUTREACH', 'Outreach'
    VOLUNTEER = 'VOLUNTEER', 'Volunteer'
    TRIBAL_PARTNERSHIP = 'TRIBAL_PARTNERSHIP', 'Tribal Partnership'
    EVENT = 'EVENT', 'Event'


# --- Social media platform and status ---
class SocialPlatform(models.TextChoices):
    FACEBOOK = 'FACEBOOK', 'Facebook'
    INSTAGRAM = 'INSTAGRAM', 'Instagram'
    TWITTER = 'TWITTER', 'Twitter'
    TIKTOK = 'TIKTOK', 'TikTok'
    LINKEDIN = 'LINKEDIN', 'LinkedIn'


class PostStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    PUBLISHED = 'PUBLISHED', 'Published'
    ARCHIVED = 'ARCHIVED', 'Archived'


# ========== MODELS ==========


class Contact(models.Model):
    """Contact record: volunteer, donor, tribal partner, media, etc."""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    contact_type = models.CharField(
        max_length=30,
        choices=ContactType.choices,
        default=ContactType.COMMUNITY_MEMBER,
    )
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='allminnesota_contacts_created',
    )

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name_plural = 'Contacts'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse('allminnesota:contact_detail', kwargs={'pk': self.pk})


class DistributionSite(models.Model):
    """Distribution site for meal delivery (Twin Cities or Greater Minnesota)."""
    site_name = models.CharField(max_length=200)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    region = models.CharField(
        max_length=30,
        choices=Region.choices,
        default=Region.TWIN_CITIES,
    )
    capacity = models.IntegerField(
        default=0,
        help_text='Max meals per distribution',
    )
    is_active = models.BooleanField(default=True)
    contact_person = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='distribution_sites',
    )
    notes = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['region', 'site_name']
        verbose_name_plural = 'Distribution Sites'

    def __str__(self):
        return self.site_name

    def get_absolute_url(self):
        return reverse('allminnesota:site_detail', kwargs={'pk': self.pk})


class BusinessPlan(models.Model):
    """Business plan with ordered sections."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='allminnesota_plans_owned',
    )
    status = models.CharField(
        max_length=20,
        choices=PlanStatus.choices,
        default=PlanStatus.DRAFT,
    )

    class Meta:
        ordering = ['-updated_date']
        verbose_name_plural = 'Business Plans'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('allminnesota:plan_detail', kwargs={'pk': self.pk})


class PlanSection(models.Model):
    """Section within a business plan (orderable)."""
    plan = models.ForeignKey(
        BusinessPlan,
        on_delete=models.CASCADE,
        related_name='sections',
    )
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        unique_together = [['plan', 'order']]
        verbose_name_plural = 'Plan Sections'

    def __str__(self):
        return f"{self.plan.title} – {self.title}"


class KPI(models.Model):
    """Key performance indicator with target and current value."""
    kpi_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0'),
    )
    current_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0'),
    )
    unit = models.CharField(
        max_length=50,
        blank=True,
        help_text='e.g. meals, dollars, volunteers, sites',
    )
    category = models.CharField(
        max_length=30,
        choices=KPICategory.choices,
        default=KPICategory.MEALS_DELIVERED,
    )
    start_date = models.DateField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='allminnesota_kpis_updated',
    )

    class Meta:
        ordering = ['category', 'kpi_name']
        verbose_name_plural = 'KPIs'

    def __str__(self):
        return self.kpi_name

    def get_absolute_url(self):
        return reverse('allminnesota:kpi_detail', kwargs={'pk': self.pk})

    def progress_percent(self):
        """Return percentage of target achieved (capped at 100 for display)."""
        if self.target_value and self.target_value != 0:
            pct = (self.current_value / self.target_value) * 100
            return min(100, float(pct))
        return 0


class KPIUpdateHistory(models.Model):
    """History log for KPI value updates."""
    kpi = models.ForeignKey(
        KPI,
        on_delete=models.CASCADE,
        related_name='update_history',
    )
    previous_value = models.DecimalField(max_digits=14, decimal_places=2)
    new_value = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='allminnesota_kpi_updates',
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = 'KPI Update History'


class Task(models.Model):
    """Task for project/operations management."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='allminnesota_tasks_assigned',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='allminnesota_tasks_created',
    )
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM,
    )
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
    )
    due_date = models.DateField(null=True, blank=True)
    category = models.CharField(
        max_length=30,
        choices=TaskCategory.choices,
        default=TaskCategory.LOGISTICS,
    )
    related_site = models.ForeignKey(
        DistributionSite,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date', 'priority', 'title']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('allminnesota:task_detail', kwargs={'pk': self.pk})

    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.due_date and self.due_date < timezone.now().date() and self.status not in (
            TaskStatus.COMPLETED,
        )


class SocialMediaPost(models.Model):
    """Social media post (draft, scheduled, or published)."""
    platform = models.CharField(
        max_length=20,
        choices=SocialPlatform.choices,
        default=SocialPlatform.FACEBOOK,
    )
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=PostStatus.choices,
        default=PostStatus.DRAFT,
    )
    scheduled_date = models.DateTimeField(null=True, blank=True)
    published_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='allminnesota_posts_created',
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    hashtags = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    related_event = models.CharField(
        max_length=200,
        blank=True,
        help_text='e.g. Keith Secola concert',
    )

    class Meta:
        ordering = ['-scheduled_date', '-created_date']
        verbose_name_plural = 'Social Media Posts'

    def __str__(self):
        return f"{self.get_platform_display()} – {self.title}"

    def get_absolute_url(self):
        return reverse('allminnesota:social_detail', kwargs={'pk': self.pk})
