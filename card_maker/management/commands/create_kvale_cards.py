"""
Management command to create Kvale card set and generate printable card images.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from card_maker.models import CardSet, Card
from card_maker.utils import generate_kvale_card


class Command(BaseCommand):
    help = 'Create Kvale card set and generate printable card images'

    def handle(self, *args, **options):
        # Create or get Kvale card set
        kvale_set, created = CardSet.objects.update_or_create(
            slug='kvale',
            defaults={
                'name': 'Kvale',
                'description': 'Printable card deck game. Cards designed to be printed and used in real card deck games.',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created card set: {kvale_set.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing card set: {kvale_set.name}'))
        
        # Path to uploaded images
        images_dir = os.path.join(settings.BASE_DIR, 'card_maker', 'kvale_set', 'uploaded_images')
        output_dir = os.path.join(settings.MEDIA_ROOT, 'cards', 'kvale')
        os.makedirs(output_dir, exist_ok=True)
        
        # Example cards data - you can expand this
        example_cards = [
            {
                'name': 'Carl',
                'slug': 'carl',
                'description': 'A determined survivor in the dungeon crawl, using wit and determination to overcome challenges.',
                'rarity': 'rare',
                'energy': 5,
                'power': 7,
                'trigger': 'When played',
                'tags': ['character', 'survivor'],
                'edition': 'First',
                'collection': 'Kvale',
                'image_file': 'Carl.webp',
            },
            {
                'name': 'Princess Donut',
                'slug': 'princess-donut',
                'description': 'A royal Persian cat with attitude and intelligence, navigating the dungeon with style.',
                'rarity': 'epic',
                'energy': 6,
                'power': 8,
                'trigger': 'On attack',
                'tags': ['character', 'royal'],
                'edition': 'First',
                'collection': 'Kvale',
                'image_file': 'Princess_Donut.webp',
            },
            {
                'name': 'Mordecai',
                'slug': 'mordecai',
                'description': 'A wise and powerful guide through the dungeon\'s mysteries.',
                'rarity': 'legendary',
                'energy': 8,
                'power': 9,
                'trigger': 'When drawn',
                'tags': ['character', 'guide'],
                'edition': 'First',
                'collection': 'Kvale',
                'image_file': 'Mordecai.webp',
            },
        ]
        
        created_count = 0
        for card_data in example_cards:
            # Find image file
            image_path = None
            image_file = card_data.pop('image_file')
            possible_paths = [
                os.path.join(images_dir, image_file),
                os.path.join(images_dir, image_file.lower()),
                os.path.join(images_dir, image_file.replace('_', ' ')),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    image_path = path
                    break
            
            if not image_path:
                self.stdout.write(self.style.WARNING(f'Image not found for {card_data["name"]}: {image_file}'))
                continue
            
            # Generate card image
            card_image_filename = f"{card_data['slug']}.png"
            card_image_path = os.path.join(output_dir, card_image_filename)
            
            try:
                generate_kvale_card(
                    title=card_data['name'],
                    rarity=card_data['rarity'],
                    album_label=card_data.get('album_label', ''),
                    energy=card_data['energy'],
                    power=card_data['power'],
                    artwork_path=image_path,
                    trigger=card_data.get('trigger', ''),
                    description=card_data['description'],
                    tags=card_data.get('tags', []),
                    edition=card_data.get('edition', ''),
                    collection=card_data.get('collection', ''),
                    output_path=card_image_path
                )
                self.stdout.write(self.style.SUCCESS(f'Generated card image: {card_image_filename}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error generating card {card_data["name"]}: {str(e)}'))
                continue
            
            # Create card in database
            card, card_created = Card.objects.update_or_create(
                card_set=kvale_set,
                slug=card_data['slug'],
                defaults={
                    'name': card_data['name'],
                    'description': card_data['description'],
                    'rarity': card_data['rarity'],
                    'card_type': 'character',
                    'energy': card_data['energy'],
                    'power': card_data['power'],
                    'trigger': card_data.get('trigger', ''),
                    'tags': card_data.get('tags', []),
                    'edition': card_data.get('edition', ''),
                    'collection': card_data.get('collection', ''),
                    'card_image': f'cards/kvale/{card_image_filename}',
                    'is_active': True,
                    'order': created_count,
                }
            )
            
            if card_created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created card: {card.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated card: {card.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created/updated {created_count} cards in the Kvale set!'))

