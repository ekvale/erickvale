from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# Constants
PERSONALITY_TYPE_CHOICES = [
    ('driver', 'Driver'),
    ('expressive', 'Expressive'),
    ('relational', 'Relational'),
    ('analyzer', 'Analyzer'),
    ('free_spirit', 'Free Spirit'),
    ('guardian', 'Guardian'),
]

TELL_CATEGORY_CHOICES = [
    ('control', 'Control'),
    ('visibility', 'Visibility'),
    ('belonging', 'Belonging'),
    ('accuracy', 'Accuracy'),
    ('freedom', 'Freedom'),
    ('safety', 'Safety'),
]

DIFFICULTY_CHOICES = [
    ('easy', 'Easy'),
    ('medium', 'Medium'),
    ('hard', 'Hard'),
]

RESPONSE_CHOICES = [
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
]


class Scenario(models.Model):
    """Game scenario with transcript and correct answers."""
    id = models.AutoField(primary_key=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    scenario_title = models.CharField(max_length=200)
    transcript = models.JSONField(help_text="List of dialogue lines")
    correct_type = models.CharField(max_length=20, choices=PERSONALITY_TYPE_CHOICES)
    tell_category = models.CharField(max_length=20, choices=TELL_CATEGORY_CHOICES)
    tell_explanation = models.TextField(help_text="Explanation of the tell(s) in the transcript")
    response_choices = models.JSONField(help_text="Dict with keys A, B, C, D mapping to response text")
    correct_response = models.CharField(max_length=1, choices=RESPONSE_CHOICES)
    response_explanation = models.TextField(help_text="Why this response is correct")
    is_feels_unheard = models.BooleanField(default=False, help_text="Variant where person feels unheard")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['difficulty', 'id']
        indexes = [
            models.Index(fields=['difficulty', 'correct_type']),
            models.Index(fields=['correct_type']),
        ]
    
    def __str__(self):
        return f"{self.scenario_title} ({self.difficulty}) - {self.get_correct_type_display()}"


class GameSession(models.Model):
    """Tracks a player's game session."""
    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    total_score = models.IntegerField(default=0)
    total_rounds = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    training_mode = models.BooleanField(default=False, help_text="Hint costs points in training mode")
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Session {self.session_id[:8]}... ({self.total_score} pts)"
    
    def get_accuracy(self):
        """Calculate accuracy percentage."""
        if self.total_rounds == 0:
            return 0
        return round((self.total_score / (self.total_rounds * 5)) * 100, 1)
    
    def get_type_accuracy(self):
        """Get accuracy breakdown by personality type."""
        rounds = self.gameround_set.all()
        type_stats = {}
        for ptype, _ in PERSONALITY_TYPE_CHOICES:
            type_rounds = rounds.filter(scenario__correct_type=ptype)
            if type_rounds.exists():
                type_correct = type_rounds.filter(type_correct=True).count()
                type_total = type_rounds.count()
                type_stats[ptype] = {
                    'correct': type_correct,
                    'total': type_total,
                    'accuracy': round((type_correct / type_total) * 100, 1) if type_total > 0 else 0
                }
        return type_stats


class GameRound(models.Model):
    """Tracks a single round/question in a game session."""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    round_number = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Player answers
    player_type_guess = models.CharField(max_length=20, choices=PERSONALITY_TYPE_CHOICES, null=True, blank=True)
    player_response_choice = models.CharField(max_length=1, choices=RESPONSE_CHOICES, null=True, blank=True)
    player_tell_category = models.CharField(max_length=20, choices=TELL_CATEGORY_CHOICES, null=True, blank=True)
    
    # Scoring
    type_correct = models.BooleanField(default=False)
    response_correct = models.BooleanField(default=False)
    tell_correct = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    hint_used = models.BooleanField(default=False)
    
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['session', 'round_number']
        unique_together = [['session', 'round_number']]
    
    def __str__(self):
        return f"Round {self.round_number} - {self.points_earned} pts"
    
    def calculate_score(self):
        """Calculate and set score for this round."""
        self.type_correct = (self.player_type_guess == self.scenario.correct_type)
        self.response_correct = (self.player_response_choice == self.scenario.correct_response)
        self.tell_correct = (self.player_tell_category == self.scenario.tell_category)
        
        points = 0
        if self.type_correct:
            points += 2
        if self.response_correct:
            points += 2
        if self.tell_correct:
            points += 1
        
        # Deduct point for hint in training mode
        if self.hint_used and self.session.training_mode:
            points = max(0, points - 1)
        
        self.points_earned = points
        return points
