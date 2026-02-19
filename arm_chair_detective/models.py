"""
Arm Chair Detective - Models for realistic detective investigation gameplay.

Each Case has one perpetrator from a large suspect pool. Users receive clues
(eyewitness accounts, 911 calls, video analysis) and filter suspects until
they identify the culprit.
"""
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone


# Choice constants for suspect attributes - designed for filtering
class SuspectAttributeChoices:
    """Centralized attribute choices for consistency across clues and filters."""
    GENDERS = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other/Unknown'),
    ]
    HAIR_COLORS = [
        ('black', 'Black'),
        ('brown', 'Brown'),
        ('blonde', 'Blonde'),
        ('red', 'Red'),
        ('gray', 'Gray/White'),
        ('bald', 'Bald'),
        ('dyed', 'Dyed/Unusual'),
        ('unknown', 'Unknown'),
    ]
    EYE_COLORS = [
        ('brown', 'Brown'),
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('hazel', 'Hazel'),
        ('gray', 'Gray'),
        ('unknown', 'Unknown'),
    ]
    BUILDS = [
        ('slim', 'Slim'),
        ('average', 'Average'),
        ('athletic', 'Athletic'),
        ('heavy', 'Heavy'),
        ('obese', 'Obese'),
        ('unknown', 'Unknown'),
    ]
    HEIGHT_RANGES = [
        ('short', 'Under 5\'6"'),
        ('medium', '5\'6" - 5\'11"'),
        ('tall', '6\' - 6\'4"'),
        ('very_tall', 'Over 6\'4"'),
        ('unknown', 'Unknown'),
    ]
    SKIN_TONES = [
        ('fair', 'Fair/Pale'),
        ('medium', 'Medium'),
        ('olive', 'Olive'),
        ('brown', 'Brown'),
        ('dark', 'Dark'),
        ('unknown', 'Unknown'),
    ]
    ACCENT_REGIONS = [
        ('local', 'Local/No accent'),
        ('southern', 'Southern US'),
        ('northeastern', 'Northeastern'),
        ('midwestern', 'Midwestern'),
        ('hispanic', 'Hispanic/Spanish'),
        ('british', 'British'),
        ('european', 'European'),
        ('asian', 'Asian'),
        ('other', 'Other/Unrecognized'),
        ('unknown', 'Unknown'),
    ]
    VEHICLE_TYPES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('pickup', 'Pickup Truck'),
        ('van', 'Van/Minivan'),
        ('coupe', 'Coupe'),
        ('hatchback', 'Hatchback'),
        ('motorcycle', 'Motorcycle'),
        ('none', 'No vehicle/On foot'),
        ('unknown', 'Unknown'),
    ]
    VEHICLE_COLORS = [
        ('white', 'White'),
        ('black', 'Black'),
        ('silver', 'Silver/Gray'),
        ('red', 'Red'),
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('brown', 'Brown/Tan'),
        ('gold', 'Gold/Beige'),
        ('unknown', 'Unknown'),
    ]
    AGE_RANGES = [
        ('teens', 'Teenager (13-19)'),
        ('twenties', '20s'),
        ('thirties', '30s'),
        ('forties', '40s'),
        ('fifties', '50s'),
        ('sixties_plus', '60+'),
        ('unknown', 'Unknown'),
    ]
    OCCUPATIONS = [
        ('delivery_driver', 'Delivery/Courier Driver'),
        ('retail', 'Retail/Service'),
        ('construction', 'Construction/Trades'),
        ('office', 'Office/Professional'),
        ('healthcare', 'Healthcare'),
        ('unemployed', 'Unemployed'),
        ('unknown', 'Unknown'),
    ]


class Suspect(models.Model):
    """
    A person in the suspect pool. One suspect per case is the perpetrator.
    Attributes are designed for filtering based on clues.
    """
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    
    # Physical description - filterable
    gender = models.CharField(max_length=1, choices=SuspectAttributeChoices.GENDERS, db_index=True)
    age_range = models.CharField(max_length=20, choices=SuspectAttributeChoices.AGE_RANGES, db_index=True)
    hair_color = models.CharField(max_length=20, choices=SuspectAttributeChoices.HAIR_COLORS, db_index=True)
    eye_color = models.CharField(max_length=20, choices=SuspectAttributeChoices.EYE_COLORS, db_index=True)
    skin_tone = models.CharField(max_length=20, choices=SuspectAttributeChoices.SKIN_TONES, db_index=True)
    build = models.CharField(max_length=20, choices=SuspectAttributeChoices.BUILDS, db_index=True)
    height_range = models.CharField(max_length=20, choices=SuspectAttributeChoices.HEIGHT_RANGES, db_index=True)
    
    # Speech / identification
    accent_region = models.CharField(max_length=20, choices=SuspectAttributeChoices.ACCENT_REGIONS, db_index=True)
    
    # Vehicle - often key in witness reports
    vehicle_type = models.CharField(max_length=20, choices=SuspectAttributeChoices.VEHICLE_TYPES, db_index=True)
    vehicle_color = models.CharField(max_length=20, choices=SuspectAttributeChoices.VEHICLE_COLORS, db_index=True)
    
    # Optional distinguishing features (free text - used in search, not strict filter)
    distinguishing_features = models.TextField(blank=True)
    occupation = models.CharField(
        max_length=20,
        choices=SuspectAttributeChoices.OCCUPATIONS,
        default='unknown',
        db_index=True,
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['gender', 'age_range', 'hair_color']),
            models.Index(fields=['vehicle_type', 'vehicle_color']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Case(models.Model):
    """
    A detective case. One suspect in the pool is the perpetrator.
    Clues are revealed in sequence to help the user narrow down suspects.
    """
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Brief case summary for the detective")
    perpetrator = models.ForeignKey(
        Suspect,
        on_delete=models.PROTECT,
        related_name='cases_as_perpetrator'
    )
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('arm_chair_detective:case_play', kwargs={'pk': self.pk})


class Clue(models.Model):
    """
    A piece of evidence for a case. Revealed in sequence.
    clue_type determines the format (eyewitness, 911 call, video, etc.)
    filter_hints is JSON describing which suspect attributes this clue implies.
    """
    CLUE_TYPES = [
        ('eyewitness', 'Eyewitness Account'),
        ('911_call', '911 Call Transcript'),
        ('video_analysis', 'Video Footage Analysis'),
        ('physical_evidence', 'Physical Evidence Report'),
        ('witness_statement', 'Additional Witness Statement'),
        ('surveillance', 'Surveillance Summary'),
        ('license_plate', 'License Plate Fragment'),
        ('cell_tower', 'Cell Tower / Location Data'),
        ('financial', 'Financial Records'),
        ('social_media', 'Social Media / Digital Footprint'),
        ('employer_records', 'Employer / Employment Records'),
        ('statement_analysis', 'Statement / Linguistic Analysis'),
        ('audio_transcript', 'Audio Transcript'),
    ]
    
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='clues')
    clue_type = models.CharField(max_length=30, choices=CLUE_TYPES)
    title = models.CharField(max_length=200, help_text="Short label for this clue")
    content = models.TextField(help_text="The actual clue content (transcript, report, etc.)")
    order = models.PositiveIntegerField(default=0, help_text="Order of revelation (1 = first)")
    is_reliable = models.BooleanField(
        default=True,
        help_text="False for red herrings / unreliable witness"
    )
    # Structured filter hints: {"hair_color": "brown", "height_range": "tall", ...}
    filter_hints = models.JSONField(
        default=dict,
        blank=True,
        help_text="Attributes this clue implies for filtering suspects"
    )
    unlock_after_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Clue only becomes available after this many hours into the case (timeline pressure)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['case', 'order', 'pk']
    
    def __str__(self):
        return f"{self.get_clue_type_display()}: {self.title}"


class GameSession(models.Model):
    """
    Optional: User's progress on a case. Tracks which clues they've seen
    and allows saving filter state. Can be extended for scoring.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='detective_sessions', null=True, blank=True)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='sessions')
    current_filters = models.JSONField(default=dict, blank=True)
    clues_revealed_count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    guessed_suspect = models.ForeignKey(
        Suspect, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='guesses'
    )
    correct = models.BooleanField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
