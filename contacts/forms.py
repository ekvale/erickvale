from django import forms

from projects.forms import TW_INPUT, TW_SELECT, TW_TEXTAREA
from projects.models import Project, Task

from .models import Contact


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = [
            'first_name',
            'last_name',
            'display_name',
            'email',
            'phone',
            'birthday',
            'company',
            'title',
            'notes',
            'avatar_url',
            'source',
            'projects',
            'tasks',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': TW_INPUT}),
            'last_name': forms.TextInput(attrs={'class': TW_INPUT}),
            'display_name': forms.TextInput(attrs={'class': TW_INPUT}),
            'email': forms.EmailInput(attrs={'class': TW_INPUT}),
            'phone': forms.TextInput(attrs={'class': TW_INPUT}),
            'birthday': forms.DateInput(attrs={'type': 'date', 'class': TW_INPUT}),
            'company': forms.TextInput(attrs={'class': TW_INPUT}),
            'title': forms.TextInput(attrs={'class': TW_INPUT}),
            'notes': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 5}),
            'avatar_url': forms.URLInput(attrs={'class': TW_INPUT}),
            'source': forms.Select(attrs={'class': TW_SELECT}),
            'projects': forms.SelectMultiple(attrs={'class': TW_SELECT, 'size': 5}),
            'tasks': forms.SelectMultiple(attrs={'class': TW_SELECT, 'size': 5}),
        }

    def __init__(self, *args, projects_queryset=None, tasks_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if projects_queryset is not None:
            self.fields['projects'].queryset = projects_queryset
        else:
            self.fields['projects'].queryset = Project.objects.none()
        if tasks_queryset is not None:
            self.fields['tasks'].queryset = tasks_queryset
        else:
            self.fields['tasks'].queryset = Task.objects.none()


class ContactImportFileForm(forms.Form):
    file = forms.FileField(
        label='Contact file',
        help_text='.vcf (vCard), LinkedIn .csv, or Facebook .json',
    )
