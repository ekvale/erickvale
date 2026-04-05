from django import forms
from django.utils import timezone

from .models import PersonalContact, PersonalContactAttachment


class PersonalContactForm(forms.ModelForm):
    class Meta:
        model = PersonalContact
        fields = [
            'display_name',
            'first_name',
            'last_name',
            'email',
            'phone',
            'phone_secondary',
            'company',
            'job_title',
            'website',
            'linkedin_url',
            'address_line1',
            'city',
            'state',
            'postal_code',
            'country',
            'birth_date',
            'relationship_kind',
            'notes',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 5}),
        }


class PersonalContactAttachmentForm(forms.ModelForm):
    class Meta:
        model = PersonalContactAttachment
        fields = ['file', 'description']


class ContactEmailMessageForm(forms.Form):
    subject = forms.CharField(max_length=200)
    body = forms.CharField(widget=forms.Textarea(attrs={'rows': 8}))


class ContactEmailScheduleForm(ContactEmailMessageForm):
    scheduled_for = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M',
        ),
        input_formats=[
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
        ],
    )

    def clean_scheduled_for(self):
        dt = self.cleaned_data['scheduled_for']
        if dt is None:
            return dt
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
