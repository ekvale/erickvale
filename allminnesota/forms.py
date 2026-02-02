"""
Forms for All Minnesota app.
"""
from django import forms
from django.contrib.auth.models import User
from .models import (
    Contact,
    DistributionSite,
    BusinessPlan,
    PlanSection,
    KPI,
    KPIUpdateHistory,
    Task,
    SocialMediaPost,
    ContactType,
    Region,
    PlanStatus,
    KPICategory,
    TaskPriority,
    TaskStatus,
    TaskCategory,
    SocialPlatform,
    PostStatus,
)


# --- Form control classes for Bootstrap 5 ---
FORM_CONTROL = {'class': 'form-control'}
FORM_SELECT = {'class': 'form-select'}
FORM_CHECK = {'class': 'form-check-input'}


class ContactForm(forms.ModelForm):
    """Create/edit Contact."""
    class Meta:
        model = Contact
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'contact_type',
            'address', 'city', 'state', 'zip_code', 'notes', 'is_active',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs=FORM_CONTROL),
            'last_name': forms.TextInput(attrs=FORM_CONTROL),
            'email': forms.EmailInput(attrs=FORM_CONTROL),
            'phone': forms.TextInput(attrs=FORM_CONTROL),
            'contact_type': forms.Select(attrs=FORM_SELECT, choices=ContactType.choices),
            'address': forms.TextInput(attrs=FORM_CONTROL),
            'city': forms.TextInput(attrs=FORM_CONTROL),
            'state': forms.TextInput(attrs=FORM_CONTROL),
            'zip_code': forms.TextInput(attrs=FORM_CONTROL),
            'notes': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs=FORM_CHECK),
        }


class ContactFilterForm(forms.Form):
    """Filter contacts by type and search."""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            **FORM_CONTROL,
            'placeholder': 'Search name, email...',
        }),
    )
    contact_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All types')] + list(ContactType.choices),
        widget=forms.Select(attrs=FORM_SELECT),
    )


class DistributionSiteForm(forms.ModelForm):
    """Create/edit DistributionSite."""
    class Meta:
        model = DistributionSite
        fields = [
            'site_name', 'address', 'city', 'state', 'zip_code', 'region',
            'capacity', 'is_active', 'contact_person', 'notes',
        ]
        widgets = {
            'site_name': forms.TextInput(attrs=FORM_CONTROL),
            'address': forms.TextInput(attrs=FORM_CONTROL),
            'city': forms.TextInput(attrs=FORM_CONTROL),
            'state': forms.TextInput(attrs=FORM_CONTROL),
            'zip_code': forms.TextInput(attrs=FORM_CONTROL),
            'region': forms.Select(attrs=FORM_SELECT, choices=Region.choices),
            'capacity': forms.NumberInput(attrs=FORM_CONTROL),
            'is_active': forms.CheckboxInput(attrs=FORM_CHECK),
            'contact_person': forms.Select(attrs=FORM_SELECT),
            'notes': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 3}),
        }


class BusinessPlanForm(forms.ModelForm):
    """Create/edit BusinessPlan."""
    class Meta:
        model = BusinessPlan
        fields = ['title', 'description', 'status']
        widgets = {
            'title': forms.TextInput(attrs=FORM_CONTROL),
            'description': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 3}),
            'status': forms.Select(attrs=FORM_SELECT, choices=PlanStatus.choices),
        }


class PlanSectionForm(forms.ModelForm):
    """Create/edit a single PlanSection."""
    class Meta:
        model = PlanSection
        fields = ['title', 'content', 'order']
        widgets = {
            'title': forms.TextInput(attrs=FORM_CONTROL),
            'content': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 5}),
            'order': forms.NumberInput(attrs=FORM_CONTROL),
        }


class KPIForm(forms.ModelForm):
    """Create/edit KPI."""
    class Meta:
        model = KPI
        fields = [
            'kpi_name', 'description', 'target_value', 'current_value',
            'unit', 'category', 'start_date', 'target_date',
        ]
        widgets = {
            'kpi_name': forms.TextInput(attrs=FORM_CONTROL),
            'description': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
            'target_value': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.01'}),
            'current_value': forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.01'}),
            'unit': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'meals, dollars, volunteers, sites'}),
            'category': forms.Select(attrs=FORM_SELECT, choices=KPICategory.choices),
            'start_date': forms.DateInput(attrs={**FORM_CONTROL, 'type': 'date'}),
            'target_date': forms.DateInput(attrs={**FORM_CONTROL, 'type': 'date'}),
        }


class KPIUpdateValueForm(forms.Form):
    """Update current value for a KPI (with history note)."""
    new_value = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        widget=forms.NumberInput(attrs={**FORM_CONTROL, 'step': '0.01'}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2, 'placeholder': 'Optional note for history'}),
    )


class KPIFilterForm(forms.Form):
    """Filter KPIs by category."""
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'All categories')] + list(KPICategory.choices),
        widget=forms.Select(attrs=FORM_SELECT),
    )


class TaskForm(forms.ModelForm):
    """Create/edit Task."""
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'assigned_to', 'priority', 'status',
            'due_date', 'category', 'related_site',
        ]
        widgets = {
            'title': forms.TextInput(attrs=FORM_CONTROL),
            'description': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 3}),
            'assigned_to': forms.Select(attrs=FORM_SELECT),
            'priority': forms.Select(attrs=FORM_SELECT, choices=TaskPriority.choices),
            'status': forms.Select(attrs=FORM_SELECT, choices=TaskStatus.choices),
            'due_date': forms.DateInput(attrs={**FORM_CONTROL, 'type': 'date'}),
            'category': forms.Select(attrs=FORM_SELECT, choices=TaskCategory.choices),
            'related_site': forms.Select(attrs=FORM_SELECT),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['related_site'].queryset = DistributionSite.objects.filter(is_active=True).order_by('site_name')


class TaskFilterForm(forms.Form):
    """Filter tasks by assignee, priority, status, category."""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'Search tasks...'}),
    )
    assigned_to = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.filter(is_active=True).order_by('username'),
        widget=forms.Select(attrs=FORM_SELECT),
        empty_label='All assignees',
    )
    priority = forms.ChoiceField(
        required=False,
        choices=[('', 'All priorities')] + list(TaskPriority.choices),
        widget=forms.Select(attrs=FORM_SELECT),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All statuses')] + list(TaskStatus.choices),
        widget=forms.Select(attrs=FORM_SELECT),
    )
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'All categories')] + list(TaskCategory.choices),
        widget=forms.Select(attrs=FORM_SELECT),
    )


class SocialMediaPostForm(forms.ModelForm):
    """Create/edit SocialMediaPost."""
    class Meta:
        model = SocialMediaPost
        fields = [
            'platform', 'title', 'content', 'status', 'scheduled_date',
            'hashtags', 'notes', 'related_event',
        ]
        widgets = {
            'platform': forms.Select(attrs=FORM_SELECT, choices=SocialPlatform.choices),
            'title': forms.TextInput(attrs=FORM_CONTROL),
            'content': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 5}),
            'status': forms.Select(attrs=FORM_SELECT, choices=PostStatus.choices),
            'scheduled_date': forms.DateTimeInput(attrs={**FORM_CONTROL, 'type': 'datetime-local'}),
            'hashtags': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2, 'placeholder': '#AllMinnesota #Community'}),
            'notes': forms.Textarea(attrs={**FORM_CONTROL, 'rows': 2}),
            'related_event': forms.TextInput(attrs={**FORM_CONTROL, 'placeholder': 'e.g. Keith Secola concert'}),
        }


class SocialMediaFilterForm(forms.Form):
    """Filter social posts by platform and status."""
    platform = forms.ChoiceField(
        required=False,
        choices=[('', 'All platforms')] + list(SocialPlatform.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All statuses')] + list(PostStatus.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
