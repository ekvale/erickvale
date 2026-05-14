"""Public site forms (erickvale.com)."""

from django import forms

TW_INPUT = (
    'mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm '
    'text-slate-900 shadow-sm focus:border-htac-teal focus:outline-none focus:ring-1 focus:ring-htac-teal'
)
TW_SELECT = TW_INPUT
TW_TEXTAREA = TW_INPUT + ' min-h-[160px]'


class SiteContactForm(forms.Form):
    INQUIRY_CHOICES = [
        ('Technical Consulting', 'Technical Consulting'),
        ('Grant Technical Assistance', 'Grant Technical Assistance'),
        ('OMOP Implementation', 'OMOP Implementation'),
        ('Federated Network Design', 'Federated Network Design'),
        ('CHNA Data Support', 'CHNA Data Support'),
        ('Partnership or Collaboration', 'Partnership or Collaboration'),
        ('Other', 'Other'),
    ]

    name = forms.CharField(
        label='Name',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': TW_INPUT, 'autocomplete': 'name'}),
    )
    organization = forms.CharField(
        label='Organization (optional)',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': TW_INPUT, 'autocomplete': 'organization'}),
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': TW_INPUT, 'autocomplete': 'email'}),
    )
    inquiry_type = forms.ChoiceField(
        label='Inquiry type',
        choices=INQUIRY_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': TW_SELECT}),
    )
    message = forms.CharField(
        label='Message',
        max_length=2000,
        required=True,
        widget=forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 6}),
    )
