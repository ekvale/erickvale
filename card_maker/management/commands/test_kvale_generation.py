"""
Test command to verify Kvale card generation works.
"""
import os
from django.core.management.base import BaseCommand
from card_maker.models import Card, CardSet


class Command(BaseCommand):
    help = 'Test Kvale card generation'

    def handle(self, *args, **options):
        # Find Kvale card set
        try:
            kvale_set = CardSet.objects.get(slug='kvale')
            self.stdout.write(self.style.SUCCESS(f'Found Kvale card set: {kvale_set.name}'))
        except CardSet.DoesNotExist:
            self.stdout.write(self.style.ERROR('Kvale card set not found!'))
            return
        
        # Get all Kvale cards
        kvale_cards = Card.objects.filter(card_set=kvale_set)
        self.stdout.write(f'Found {kvale_cards.count()} cards in Kvale set')
        
        # Try to regenerate each card
        for card in kvale_cards:
            self.stdout.write(f'\nProcessing: {card.name}')
            self.stdout.write(f'  Card Set: {card.card_set.slug}')
            self.stdout.write(f'  Energy: {card.energy}, Power: {card.power}')
            self.stdout.write(f'  Has card_image: {bool(card.card_image)}')
            
            if card.card_image:
                try:
                    self.stdout.write(f'  Image path: {card.card_image.path}')
                    self.stdout.write(f'  Image exists: {os.path.exists(card.card_image.path)}')
                    self.stdout.write(f'  Image name: {card.card_image.name}')
                except Exception as e:
                    self.stdout.write(f'  Error checking image: {e}')
            
            # Try to generate
            success = card.generate_kvale_card_image()
            if success:
                card.save(update_fields=['card_image'])
                self.stdout.write(self.style.SUCCESS(f'  ✓ Successfully generated card image'))
            else:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed to generate card image'))
        
        self.stdout.write(self.style.SUCCESS('\nDone!'))

