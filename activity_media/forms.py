from django import forms
from .models import MediaItem, ActivityTag


class MediaItemForm(forms.ModelForm):
    """Form for uploading media items."""
    
    # Custom field for activity tags as comma-separated or checkboxes
    activity_tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter tags separated by commas',
            'class': 'form-control'
        }),
        help_text='Enter activity tags separated by commas, or select from existing tags below'
    )
    
    class Meta:
        model = MediaItem
        fields = ['media_type', 'file', 'title', 'description', 'latitude', 'longitude', 
                  'location_name', 'activity_tags', 'is_public']
        widgets = {
            'media_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,video/*'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Optional description'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'e.g., 44.9778'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'e.g., -93.2650'}),
            'location_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional location name/address'}),
            'activity_tags': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'latitude': 'Enter latitude (e.g., 44.9778)',
            'longitude': 'Enter longitude (e.g., -93.2650)',
            'activity_tags': 'Select existing activity tags',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make activity_tags optional
        self.fields['activity_tags'].required = False
        self.fields['activity_tags'].queryset = ActivityTag.objects.all().order_by('name')
        
        # Make location optional
        self.fields['latitude'].required = False
        self.fields['longitude'].required = False
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 100MB for videos, 10MB for images)
            max_size = 100 * 1024 * 1024  # 100MB
            if file.size > max_size:
                raise forms.ValidationError(f'File size cannot exceed {max_size / (1024*1024):.0f}MB.')
        return file
