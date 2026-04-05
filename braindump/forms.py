from django import forms

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
