"""
Django models for qualitative literary analysis framework.
"""
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import FileExtensionValidator
from ckeditor_uploader.fields import RichTextUploadingField


class LiteraryWork(models.Model):
    """Represents an uploaded literary text."""
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=200)
    text_file = models.FileField(
        upload_to='literary_texts/',
        validators=[FileExtensionValidator(allowed_extensions=['txt'])]
    )
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='literary_works')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    text_length = models.IntegerField(default=0, help_text='Character count')
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Literary Work'
        verbose_name_plural = 'Literary Works'
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
    def get_absolute_url(self):
        return reverse('literary_analysis:work_detail', kwargs={'pk': self.pk})
    
    def get_segment(self, start_pos, end_pos):
        """Extract a text segment from the file."""
        try:
            if not self.text_file:
                return ""
            # Read file using path directly (works across Django versions)
            with open(self.text_file.path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Decode Unicode escape sequences if present
            if '\\u' in text or '\\U' in text:
                import re
                def replace_unicode(match):
                    code = match.group(1)
                    try:
                        if len(code) == 4:
                            return chr(int(code, 16))
                        elif len(code) == 8:
                            return chr(int(code, 16))
                    except (ValueError, OverflowError):
                        return match.group(0)
                    return match.group(0)
                text = re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode, text)
                text = re.sub(r'\\U([0-9a-fA-F]{8})', replace_unicode, text)
                text = text.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                text = text.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
            
            return text[start_pos:end_pos]
        except Exception:
            return ""


class CodebookTemplate(models.Model):
    """Template codebook for different types of analysis."""
    TEMPLATE_TYPES = [
        ('dhalgren', 'Dhalgren Specialized Analyzer'),
        ('divine_comedy', 'Divine Comedy Analyzer'),
        ('custom', 'Custom Codebook'),
        ('general', 'General Narrative Fiction'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, default='custom')
    is_public = models.BooleanField(default=False, help_text='Share with other users')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='codebooks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Codebook Template'
        verbose_name_plural = 'Codebook Templates'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('literary_analysis:codebook_detail', kwargs={'pk': self.pk})


class Code(models.Model):
    """A code for qualitative analysis."""
    CODE_TYPES = [
        ('descriptive', 'Descriptive'),
        ('process', 'Process'),
        ('emotion', 'Emotion'),
        ('values', 'Values'),
        ('structure', 'Structure'),
    ]
    
    codebook = models.ForeignKey(CodebookTemplate, on_delete=models.CASCADE, related_name='codes')
    code_name = models.CharField(max_length=100, help_text='Unique identifier like "URBAN_DECAY"')
    code_type = models.CharField(max_length=20, choices=CODE_TYPES, default='descriptive')
    definition = models.TextField(help_text='What this code captures')
    examples = models.JSONField(default=list, blank=True, help_text='Example applications')
    parent_code = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcodes')
    order = models.IntegerField(default=0, help_text='Display order')
    
    class Meta:
        ordering = ['codebook', 'order', 'code_name']
        unique_together = [['codebook', 'code_name']]
        verbose_name = 'Code'
        verbose_name_plural = 'Codes'
    
    def __str__(self):
        return f"{self.codebook.name}: {self.code_name}"


class Analysis(models.Model):
    """A qualitative analysis of a literary work."""
    literary_work = models.ForeignKey(LiteraryWork, on_delete=models.CASCADE, related_name='analyses')
    codebook = models.ForeignKey(CodebookTemplate, on_delete=models.CASCADE, related_name='analyses')
    analyst = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analyses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    json_data = models.JSONField(default=dict, blank=True, help_text='Complete analysis data')
    report_html = models.TextField(blank=True, help_text='Cached HTML report')
    report_generated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = 'Analyses'
        unique_together = [['literary_work', 'codebook', 'analyst']]
    
    def __str__(self):
        return f"Analysis of {self.literary_work.title} using {self.codebook.name}"
    
    def get_absolute_url(self):
        return reverse('literary_analysis:analysis_detail', kwargs={'pk': self.pk})
    
    def get_code_frequency(self):
        """Calculate code frequency from coded segments."""
        from collections import Counter
        segments = self.coded_segments.all()
        frequency = Counter()
        for segment in segments:
            for code in segment.codes.all():
                frequency[code.code_name] += 1
        return dict(frequency)


class CodedSegment(models.Model):
    """A segment of text that has been coded."""
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='coded_segments')
    start_position = models.IntegerField()
    end_position = models.IntegerField()
    text_excerpt = models.TextField(help_text='The actual text segment')
    location = models.CharField(max_length=200, blank=True, help_text='Descriptive location like "Page 45, Chapter 3"')
    memo = RichTextUploadingField(blank=True, help_text='Analytical note about this segment')
    codes = models.ManyToManyField(Code, related_name='segments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coded_segments')
    
    class Meta:
        ordering = ['start_position']
        verbose_name = 'Coded Segment'
        verbose_name_plural = 'Coded Segments'
    
    def __str__(self):
        return f"Segment {self.start_position}-{self.end_position}: {self.text_excerpt[:50]}..."
    
    def get_code_names(self):
        """Return list of code names applied to this segment."""
        return [code.code_name for code in self.codes.all()]


class AnalyticalMemo(models.Model):
    """Standalone analytical memos for an analysis."""
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='memos')
    title = models.CharField(max_length=200)
    content = RichTextUploadingField(help_text='Analytical memo content with rich text editor')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytical_memos')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Analytical Memo'
        verbose_name_plural = 'Analytical Memos'
    
    def __str__(self):
        return f"{self.title} ({self.analysis})"
