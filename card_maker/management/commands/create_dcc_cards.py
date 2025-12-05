from django.core.management.base import BaseCommand
from card_maker.models import CardSet, Card


class Command(BaseCommand):
    help = 'Create example cards from Dungeon Crawler Carl Book 1'

    def handle(self, *args, **options):
        # Create or get the card set
        card_set, created = CardSet.objects.get_or_create(
            slug='dungeon-crawler-carl-book-1',
            defaults={
                'name': 'Dungeon Crawler Carl - Book 1',
                'description': 'Characters from the first book of the Dungeon Crawler Carl series by Matt Dinniman.',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created card set: {card_set.name}'))
        else:
            self.stdout.write(f'Using existing card set: {card_set.name}')
        
        # Define characters with their stats
        characters = [
            {
                'name': 'Carl',
                'slug': 'carl',
                'description': 'A former soldier turned dungeon crawler. Carl is pragmatic, resourceful, and determined to survive the deadly dungeon system. He starts with basic stats but quickly adapts to the challenges.',
                'card_type': 'character',
                'rarity': 'legendary',
                'level': 1,
                'strength': 6,
                'intelligence': 3,
                'constitution': 5,
                'dexterity': 5,
                'charisma': 4,
                'abilities': 'Survival Instinct - Adapts quickly to dangerous situations. Resourceful - Makes use of available items and environment.',
                'order': 1,
            },
            {
                'name': 'Princess Donut',
                'slug': 'princess-donut',
                'description': 'A former show cat who gained intelligence in the dungeon. Donut is vain, sassy, and surprisingly capable. Despite her attitude, she proves to be a valuable companion.',
                'card_type': 'character',
                'rarity': 'epic',
                'level': 1,
                'strength': 2,
                'intelligence': 8,
                'constitution': 3,
                'dexterity': 7,
                'charisma': 9,
                'abilities': 'High Intelligence - Can understand and communicate complex ideas. High Charisma - Natural leader and influencer. Agile - Quick and nimble.',
                'order': 2,
            },
            {
                'name': 'Mongo',
                'slug': 'mongo',
                'description': 'A massive, loyal companion who follows Carl and Donut. Mongo is incredibly strong and protective, making him a valuable asset in combat situations.',
                'card_type': 'creature',
                'rarity': 'rare',
                'level': 1,
                'strength': 10,
                'intelligence': 2,
                'constitution': 9,
                'dexterity': 4,
                'charisma': 3,
                'abilities': 'Massive Strength - Extremely powerful physical attacks. High Constitution - Can take significant damage. Loyal - Fights to protect allies.',
                'order': 3,
            },
            {
                'name': 'Mordecai',
                'slug': 'mordecai',
                'description': 'A knowledgeable NPC who provides guidance and information about the dungeon system. Mordecai helps Carl understand the rules and mechanics of the crawl.',
                'card_type': 'character',
                'rarity': 'rare',
                'level': 1,
                'strength': 4,
                'intelligence': 9,
                'constitution': 4,
                'dexterity': 5,
                'charisma': 6,
                'abilities': 'Dungeon Knowledge - Extensive understanding of dungeon mechanics. Guidance - Provides valuable information and advice.',
                'order': 4,
            },
            {
                'name': 'The Crawl',
                'slug': 'the-crawl',
                'description': 'The deadly dungeon system that traps and challenges crawlers. A merciless AI-controlled environment designed to entertain viewers while eliminating participants.',
                'card_type': 'location',
                'rarity': 'legendary',
                'level': 1,
                'strength': 0,
                'intelligence': 10,
                'constitution': 10,
                'dexterity': 0,
                'charisma': 0,
                'abilities': 'System Control - Controls all aspects of the dungeon. Adaptive Difficulty - Adjusts challenges based on crawler performance. Merciless - Shows no mercy to participants.',
                'order': 5,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for char_data in characters:
            card, created = Card.objects.update_or_create(
                card_set=card_set,
                slug=char_data['slug'],
                defaults={
                    'name': char_data['name'],
                    'description': char_data['description'],
                    'card_type': char_data['card_type'],
                    'rarity': char_data['rarity'],
                    'level': char_data['level'],
                    'strength': char_data['strength'],
                    'intelligence': char_data['intelligence'],
                    'constitution': char_data['constitution'],
                    'dexterity': char_data['dexterity'],
                    'charisma': char_data['charisma'],
                    'abilities': char_data['abilities'],
                    'order': char_data['order'],
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created card: {card.name}'))
            else:
                updated_count += 1
                self.stdout.write(f'Updated card: {card.name}')
        
        self.stdout.write(self.style.SUCCESS(
            f'\nCompleted! Created {created_count} new cards, updated {updated_count} existing cards.'
        ))
        self.stdout.write(f'Card Set: {card_set.name} ({card_set.cards.count()} total cards)')



