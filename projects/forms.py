import mimetypes
import os

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    Comment,
    Contact,
    Document,
    Event,
    Project,
    ProjectMembership,
    Task,
)

User = get_user_model()

TW_INPUT = (
    'mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm '
    'text-slate-900 shadow-sm focus:border-htac-teal focus:outline-none focus:ring-1 focus:ring-htac-teal'
)
TW_SELECT = TW_INPUT
TW_TEXTAREA = TW_INPUT + ' min-h-[120px]'
TW_CHECK = 'h-4 w-4 rounded border-slate-300 text-htac-teal focus:ring-htac-teal'

MAX_DOCUMENT_BYTES = 50 * 1024 * 1024
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.csv', '.png', '.jpg', '.jpeg'}


def _project_member_user_ids(project):
    ids = set(project.memberships.values_list('user_id', flat=True))
    if project.owner_id:
        ids.add(project.owner_id)
    return ids


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'status', 'priority', 'owner', 'start_date', 'due_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': TW_INPUT}),
            'description': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 5}),
            'status': forms.Select(attrs={'class': TW_SELECT}),
            'priority': forms.Select(attrs={'class': TW_SELECT}),
            'owner': forms.Select(attrs={'class': TW_SELECT}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': TW_INPUT}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': TW_INPUT}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'parent_task',
            'title',
            'description',
            'status',
            'priority',
            'assignees',
            'due_date',
            'estimated_hours',
            'order',
        ]
        widgets = {
            'parent_task': forms.Select(attrs={'class': TW_SELECT}),
            'title': forms.TextInput(attrs={'class': TW_INPUT}),
            'description': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 5}),
            'status': forms.Select(attrs={'class': TW_SELECT}),
            'priority': forms.Select(attrs={'class': TW_SELECT}),
            'assignees': forms.SelectMultiple(attrs={'class': TW_SELECT, 'size': 6}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': TW_INPUT}),
            'estimated_hours': forms.NumberInput(attrs={'class': TW_INPUT, 'step': '0.25'}),
            'order': forms.NumberInput(attrs={'class': TW_INPUT}),
        }

    def __init__(self, *args, project=None, task_instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        if project:
            member_ids = _project_member_user_ids(project)
            self.fields['assignees'].queryset = User.objects.filter(id__in=member_ids).order_by(
                'username'
            )
            qs = Task.objects.filter(project=project, parent_task__isnull=True)
            if task_instance and task_instance.pk:
                qs = qs.exclude(pk=task_instance.pk)
            self.fields['parent_task'].queryset = qs.order_by('title')
            self.fields['parent_task'].required = False
        else:
            self.fields['assignees'].queryset = User.objects.none()
            self.fields['parent_task'].queryset = Task.objects.none()


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 4}),
        }


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': TW_INPUT}),
            'file': forms.ClearableFileInput(
                attrs={
                    'class': TW_INPUT,
                }
            ),
        }

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if not f:
            raise forms.ValidationError('Please choose a file to upload.')
        name = getattr(f, 'name', '') or ''
        ext = os.path.splitext(name.lower())[1]
        if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
            raise forms.ValidationError(
                'Allowed file types: PDF, DOCX, XLSX, CSV, PNG, JPG.'
            )
        size = getattr(f, 'size', 0) or 0
        if size > MAX_DOCUMENT_BYTES:
            raise forms.ValidationError('File must be 50MB or smaller.')
        return f

    def save(self, commit=True):
        obj = super().save(commit=False)
        f = self.cleaned_data.get('file')
        if f:
            obj.file_size = getattr(f, 'size', 0) or 0
            guessed, _encoding = mimetypes.guess_type(f.name)
            obj.mime_type = guessed or ''
        if commit:
            obj.full_clean()
            obj.save()
            self.save_m2m()
        return obj


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = [
            'first_name',
            'last_name',
            'organization',
            'title',
            'email',
            'phone',
            'contact_type',
            'notes',
            'projects',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': TW_INPUT}),
            'last_name': forms.TextInput(attrs={'class': TW_INPUT}),
            'organization': forms.TextInput(attrs={'class': TW_INPUT}),
            'title': forms.TextInput(attrs={'class': TW_INPUT}),
            'email': forms.EmailInput(attrs={'class': TW_INPUT}),
            'phone': forms.TextInput(attrs={'class': TW_INPUT}),
            'contact_type': forms.Select(attrs={'class': TW_SELECT}),
            'notes': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 5}),
            'projects': forms.SelectMultiple(attrs={'class': TW_SELECT, 'size': 6}),
        }

    def __init__(self, *args, accessible_projects_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if accessible_projects_queryset is not None:
            self.fields['projects'].queryset = accessible_projects_queryset


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'event_type',
            'project',
            'task',
            'attendees',
            'start_datetime',
            'end_datetime',
            'all_day',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': TW_INPUT}),
            'description': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 4}),
            'event_type': forms.Select(attrs={'class': TW_SELECT}),
            'project': forms.Select(attrs={'class': TW_SELECT}),
            'task': forms.Select(attrs={'class': TW_SELECT}),
            'attendees': forms.SelectMultiple(attrs={'class': TW_SELECT, 'size': 6}),
            'start_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': TW_INPUT},
                format='%Y-%m-%dT%H:%M',
            ),
            'end_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': TW_INPUT},
                format='%Y-%m-%dT%H:%M',
            ),
            'all_day': forms.CheckboxInput(attrs={'class': TW_CHECK}),
        }

    def __init__(self, *args, user=None, accessible_projects_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        if accessible_projects_queryset is not None:
            self.fields['project'].queryset = accessible_projects_queryset
        self.fields['project'].required = False
        self.fields['task'].required = False
        self.fields['task'].queryset = Task.objects.none()
        proj = None
        if self.data.get('project'):
            try:
                proj = Project.objects.get(pk=self.data.get('project'))
            except (Project.DoesNotExist, ValueError, TypeError):
                proj = None
        elif self.initial.get('project'):
            try:
                proj = Project.objects.get(pk=self.initial['project'])
            except (Project.DoesNotExist, ValueError, TypeError):
                proj = None
        elif getattr(self.instance, 'project_id', None):
            proj = self.instance.project
        if proj:
            self.fields['task'].queryset = Task.objects.filter(project=proj).order_by('title')
        self.fields['attendees'].queryset = User.objects.filter(is_active=True).order_by('username')
        for fname in ('start_datetime', 'end_datetime'):
            fld = self.fields.get(fname)
            if fld:
                fld.input_formats = [
                    '%Y-%m-%dT%H:%M',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M',
                ]

    def clean_start_datetime(self):
        dt = self.cleaned_data.get('start_datetime')
        if dt is None:
            return dt
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    def clean_end_datetime(self):
        dt = self.cleaned_data.get('end_datetime')
        if dt is None:
            return dt
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt


class ProjectMembershipForm(forms.ModelForm):
    class Meta:
        model = ProjectMembership
        fields = ['user', 'role']
        widgets = {
            'user': forms.Select(attrs={'class': TW_SELECT}),
            'role': forms.Select(attrs={'class': TW_SELECT}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        if project:
            existing = set(project.memberships.values_list('user_id', flat=True))
            if project.owner_id:
                existing.add(project.owner_id)
            self.fields['user'].queryset = User.objects.exclude(id__in=existing).order_by(
                'username'
            )
