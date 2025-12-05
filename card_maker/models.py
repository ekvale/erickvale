from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator


class CardSet(models.Model):
    """A collection of cards (e.g., Dungeon Crawler Carl Book 1)."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='card_sets/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Card Set'
        verbose_name_plural = 'Card Sets'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('card_maker:set_detail', kwargs={'slug': self.slug})


class Card(models.Model):
    """Individual card with stats, image, and description."""
    
    RARITY_CHOICES = [
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]
    
    TYPE_CHOICES = [
        ('character', 'Character'),
        ('creature', 'Creature'),
        ('item', 'Item'),
        ('spell', 'Spell'),
        ('ability', 'Ability'),
        ('location', 'Location'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    card_set = models.ForeignKey(CardSet, on_delete=models.CASCADE, related_name='cards')
    card_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='character')
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')
    
    # Visual
    card_image = models.ImageField(upload_to='cards/', help_text='Main card image displayed prominently')
    card_image_alt = models.CharField(max_length=200, blank=True, help_text='Alt text for accessibility')
    
    # Description (flavor text like Magic: The Gathering)
    description = models.TextField(help_text='Card description/flavor text')
    
    # Dungeon Crawler Carl Stats
    level = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(100)], help_text='Character level')
    strength = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text='STR - Strength stat')
    intelligence = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text='INT - Intelligence stat')
    constitution = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text='CON - Constitution stat')
    dexterity = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text='DEX - Dexterity stat')
    charisma = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text='CHR - Charisma stat')
    
    # Additional flexible stats (stored as JSON or text)
    additional_stats = models.JSONField(default=dict, blank=True, help_text='Additional stats in JSON format')
    
    # Abilities/Skills (rich text)
    abilities = models.TextField(blank=True, help_text='Card abilities or special skills')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text='Display order within set')
    
    class Meta:
        ordering = ['card_set', 'order', 'name']
        unique_together = [['card_set', 'slug']]
        verbose_name = 'Card'
        verbose_name_plural = 'Cards'
    
    def __str__(self):
        return f"{self.name} ({self.card_set.name})"
    
    def get_absolute_url(self):
        return reverse('card_maker:card_detail', kwargs={'set_slug': self.card_set.slug, 'card_slug': self.slug})
    
    @property
    def total_stats(self):
        """Calculate total stat points."""
        return (
            self.strength + self.intelligence + self.constitution + 
            self.dexterity + self.charisma
        )
    
    @property
    def stat_summary(self):
        """Get a summary of DCC stats."""
        stats = []
        if self.strength > 0:
            stats.append(f"STR: {self.strength}")
        if self.intelligence > 0:
            stats.append(f"INT: {self.intelligence}")
        if self.constitution > 0:
            stats.append(f"CON: {self.constitution}")
        if self.dexterity > 0:
            stats.append(f"DEX: {self.dexterity}")
        if self.charisma > 0:
            stats.append(f"CHR: {self.charisma}")
        return " | ".join(stats) if stats else "No stats"
    
    @property
    def stat_display(self):
        """Get formatted stat display for card."""
        return {
            'STR': self.strength,
            'INT': self.intelligence,
            'CON': self.constitution,
            'DEX': self.dexterity,
            'CHR': self.charisma,
        }
