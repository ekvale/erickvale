from django import forms
from .models import Source, Article, Tag


class SourceForm(forms.ModelForm):
    class Meta:
        model = Source
        fields = ['url', 'source_type', 'name', 'is_active', 'fetch_interval_hours', 'default_tags']


class ArticleFilterForm(forms.Form):
    q = forms.CharField(required=False, label='Search', widget=forms.TextInput(attrs={'placeholder': 'Search…'}))
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    source = forms.ModelChoiceField(
        queryset=Source.objects.filter(is_active=True),
        required=False,
        empty_label='All sources',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))


class AddByUrlForm(forms.Form):
    url = forms.URLField(
        label='Article URL',
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://…'})
    )
    title = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional, will try to fetch from URL'})
    )
    summary = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional summary'})
    )
