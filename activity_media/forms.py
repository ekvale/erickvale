from django import forms
from .models import MediaItem, ActivityTag
from .utils import extract_location_from_file
import os


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
        
        # Hide media_type field - we'll auto-detect it
        self.fields['media_type'].widget = forms.HiddenInput()
        self.fields['media_type'].required = False
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Auto-detect media type from file extension
            file_name = file.name.lower()
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
            
            is_image = any(file_name.endswith(ext) for ext in image_extensions)
            is_video = any(file_name.endswith(ext) for ext in video_extensions)
            
            if is_image:
                self.cleaned_data['media_type'] = 'photo'
            elif is_video:
                self.cleaned_data['media_type'] = 'video'
            else:
                # Try to detect from MIME type as fallback
                if hasattr(file, 'content_type'):
                    if file.content_type.startswith('image/'):
                        self.cleaned_data['media_type'] = 'photo'
                    elif file.content_type.startswith('video/'):
                        self.cleaned_data['media_type'] = 'video'
                    else:
                        raise forms.ValidationError('Unsupported file type. Please upload an image or video.')
                else:
                    raise forms.ValidationError('Could not determine file type. Please ensure the file has a valid extension.')
            
            # Check file size (max 100MB)
            max_size = 100 * 1024 * 1024  # 100MB
            if file.size > max_size:
                raise forms.ValidationError(f'File size cannot exceed {max_size / (1024*1024):.0f}MB.')
        return file
    
    def clean(self):
        cleaned_data = super().clean()
        # Ensure media_type is set from file if not already set
        if not cleaned_data.get('media_type') and cleaned_data.get('file'):
            # This should have been set in clean_file, but double-check
            file = cleaned_data.get('file')
            file_name = file.name.lower()
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
            
            if any(file_name.endswith(ext) for ext in image_extensions):
                cleaned_data['media_type'] = 'photo'
            elif any(file_name.endswith(ext) for ext in video_extensions):
                cleaned_data['media_type'] = 'video'
        return cleaned_data
    
    def save(self, commit=True):
        """Override save to handle creating new tags and extracting location from EXIF."""
        media_item = super().save(commit=False)
        
        # Save first to get file path, then extract location if needed
        if commit:
            media_item.save()
            
            # Extract location from file metadata if not already provided
            if media_item.file and not media_item.latitude and not media_item.longitude:
                try:
                    file_path = media_item.file.path
                    if file_path and os.path.exists(file_path):
                        lat, lon = extract_location_from_file(file_path, media_item.media_type)
                        if lat and lon:
                            media_item.latitude = lat
                            media_item.longitude = lon
                            media_item.save(update_fields=['latitude', 'longitude'])
                except Exception as e:
                    # If extraction fails, just continue without location
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Could not extract location from file: {e}")
            
            # Save many-to-many relationships (activity_tags)
            self.save_m2m()
            
            # Handle creating new tags from activity_tags_input if provided
            if hasattr(self, 'cleaned_data') and 'activity_tags_input' in self.cleaned_data:
                tags_input = self.cleaned_data.get('activity_tags_input', '').strip()
                if tags_input:
                    # Split by comma and create tags that don't exist
                    tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                    for tag_name in tag_names:
                        tag, created = ActivityTag.objects.get_or_create(name=tag_name)
                        if tag not in media_item.activity_tags.all():
                            media_item.activity_tags.add(tag)
        
        return media_item
    
