from django import forms

from .models import NewsletterSubscriber


class EventSubmissionForm(forms.Form):
    """Public suggestion form (does not auto-publish; could email or save to a model later)."""
    title = forms.CharField(max_length=500, label='Event title')
    year = forms.IntegerField(min_value=1492, max_value=2100, label='Year (approx.)')
    location = forms.CharField(max_length=300, required=False, label='Location')
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 6}), label='Description')
    submitter_email = forms.EmailField(required=False, label='Your email (optional)')
    source_url = forms.URLField(required=False, label='Source link (optional)')


class EducatorNewsletterForm(forms.ModelForm):
    """Sign up for educator / partner digest emails (stored in admin; wire ESP separately)."""

    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(
                attrs={
                    'placeholder': 'you@school.edu',
                    'autocomplete': 'email',
                    'class': '',
                }
            ),
        }
