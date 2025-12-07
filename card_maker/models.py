from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.files import File
import os
import tempfile
from django.conf import settings


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
    
    # Kvale card format fields
    energy = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text='Energy stat for Kvale cards')
    power = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text='Power stat for Kvale cards')
    trigger = models.CharField(max_length=100, blank=True, help_text='Ability trigger text for Kvale cards')
    album_label = models.CharField(max_length=100, blank=True, help_text='Album label for Kvale cards')
    tags = models.JSONField(default=list, blank=True, help_text='Tags as list of strings (e.g., ["nature", "science"])')
    edition = models.CharField(max_length=100, blank=True, help_text='Edition name for Kvale cards')
    collection = models.CharField(max_length=100, blank=True, help_text='Collection name for Kvale cards')
    
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
    
    def generate_kvale_card_image(self, artwork_path=None):
        """Generate the full card image for Kvale cards."""
        if self.card_set.slug != 'kvale':
            return False
        
        try:
            from card_maker.utils import generate_kvale_card
            
            # Get artwork path
            if not artwork_path:
                # First try: use the current card_image if it exists and is not already a generated card
                if self.card_image and os.path.exists(self.card_image.path):
                    # Check if it's already a generated card (has "_card" in filename)
                    if "_card" not in self.card_image.name:
                        artwork_path = self.card_image.path
                
                # Second try: find artwork in uploaded_images directory
                if not artwork_path:
                    images_dir = os.path.join(settings.BASE_DIR, 'card_maker', 'kvale_set', 'uploaded_images')
                    # Try common image names based on card name
                    possible_names = [
                        f"{self.name}.webp",
                        f"{self.name}.jpg",
                        f"{self.name}.png",
                        f"{self.slug}.webp",
                        f"{self.slug}.jpg",
                        f"{self.slug}.png",
                    ]
                    for name in possible_names:
                        test_path = os.path.join(images_dir, name)
                        if os.path.exists(test_path):
                            artwork_path = test_path
                            break
            
            if not artwork_path or not os.path.exists(artwork_path):
                return False
            
            # Generate card to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                temp_path = tmp_file.name
            
            generate_kvale_card(
                title=self.name,
                rarity=self.rarity,
                album_label=self.album_label or '',
                energy=self.energy,
                power=self.power,
                artwork_path=artwork_path,
                trigger=self.trigger or '',
                description=self.description,
                tags=self.tags if isinstance(self.tags, list) else [],
                edition=self.edition or '',
                collection=self.collection or '',
                output_path=temp_path
            )
            
            # Save generated card image
            with open(temp_path, 'rb') as f:
                filename = f"{self.slug}_card.png"
                self.card_image.save(filename, File(f), save=False)
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
            return True
        except Exception as e:
            import traceback
            print(f"Error generating Kvale card image: {e}")
            print(traceback.format_exc())
            return False
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate card image for Kvale cards."""
        # Only auto-generate for Kvale cards
        is_kvale = hasattr(self, 'card_set_id') and self.card_set_id
        if is_kvale:
            try:
                # Get the card_set to check slug
                if not hasattr(self, '_card_set_cache'):
                    from django.db import models
                    self._card_set_cache = self.card_set
                is_kvale = self._card_set_cache.slug == 'kvale'
            except:
                is_kvale = False
        
        # Save first to get pk and ensure card_image is saved to disk
        super().save(*args, **kwargs)
        
        # Generate card image if it's a Kvale card
        if is_kvale:
            # Check if card_image exists and is not already a generated card
            artwork_path = None
            if self.card_image:
                try:
                    # Check if it's already a generated card
                    if "_card" not in str(self.card_image.name):
                        # Use current image as artwork if it exists on disk
                        if hasattr(self.card_image, 'path') and os.path.exists(self.card_image.path):
                            artwork_path = self.card_image.path
                except:
                    pass
            
            # Try to generate the card
            if self.generate_kvale_card_image(artwork_path=artwork_path):
                # Save again to update the card_image field
                super().save(update_fields=['card_image'])
