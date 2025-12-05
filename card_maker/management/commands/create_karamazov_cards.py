from django.core.management.base import BaseCommand
from card_maker.models import CardSet, Card


class Command(BaseCommand):
    help = 'Create example cards from The Brothers Karamazov by Fyodor Dostoevsky'

    def handle(self, *args, **options):
        # Create or get the card set
        card_set, created = CardSet.objects.get_or_create(
            slug='the-brothers-karamazov',
            defaults={
                'name': 'The Brothers Karamazov',
                'description': 'Main characters from Fyodor Dostoevsky\'s masterpiece novel, The Brothers Karamazov. A philosophical and psychological exploration of faith, doubt, and morality.',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created card set: {card_set.name}'))
        else:
            self.stdout.write(f'Using existing card set: {card_set.name}')
        
        # Define characters with their stats based on their traits in the novel
        characters = [
            {
                'name': 'Fyodor Pavlovich Karamazov',
                'slug': 'fyodor-karamazov',
                'description': 'The debauched and cynical father of the Karamazov brothers. A man driven by base desires, greed, and a complete lack of moral restraint. His actions set the stage for the family tragedy.',
                'card_type': 'character',
                'rarity': 'rare',
                'level': 1,
                'strength': 4,
                'intelligence': 6,
                'constitution': 5,
                'dexterity': 3,
                'charisma': 7,
                'abilities': 'Cunning - Manipulates others for personal gain. Debauchery - Indulges in excess without restraint. Wealth - Uses money to control situations.',
                'order': 1,
            },
            {
                'name': 'Dmitri Karamazov',
                'slug': 'dmitri-karamazov',
                'description': 'The passionate and impulsive eldest son. Mitya is torn between his desires and his conscience, capable of both great love and violent rage. His struggle with honor and passion drives much of the novel.',
                'card_type': 'character',
                'rarity': 'epic',
                'level': 1,
                'strength': 8,
                'intelligence': 5,
                'constitution': 7,
                'dexterity': 6,
                'charisma': 8,
                'abilities': 'Passionate - Acts with intense emotion and conviction. Duelist - Skilled in combat and confrontation. Tormented - Struggles between desire and morality.',
                'order': 2,
            },
            {
                'name': 'Ivan Karamazov',
                'slug': 'ivan-karamazov',
                'description': 'The intellectual middle son, a rationalist who grapples with profound philosophical questions. Ivan\'s struggle with faith, the problem of evil, and his own moral responsibility forms the novel\'s philosophical core.',
                'card_type': 'character',
                'rarity': 'legendary',
                'level': 1,
                'strength': 5,
                'intelligence': 10,
                'constitution': 4,
                'dexterity': 5,
                'charisma': 6,
                'abilities': 'Intellectual - Master of philosophical reasoning and debate. The Grand Inquisitor - Questions faith and morality deeply. Internal Conflict - Struggles with the consequences of ideas.',
                'order': 3,
            },
            {
                'name': 'Alyosha Karamazov',
                'slug': 'alyosha-karamazov',
                'description': 'The youngest son, a novice monk known for his kindness, faith, and spiritual purity. Alyosha serves as the moral center of the novel, embodying love, forgiveness, and hope.',
                'card_type': 'character',
                'rarity': 'legendary',
                'level': 1,
                'strength': 4,
                'intelligence': 7,
                'constitution': 6,
                'dexterity': 5,
                'charisma': 10,
                'abilities': 'Compassion - Shows unconditional love and understanding. Faith - Strong spiritual conviction and hope. Mediator - Brings people together and resolves conflicts.',
                'order': 4,
            },
            {
                'name': 'Smerdyakov',
                'slug': 'smerdyakov',
                'description': 'The illegitimate son, raised as a servant. Smerdyakov is intelligent but resentful, capable of great cunning and manipulation. His actions have devastating consequences for the family.',
                'card_type': 'character',
                'rarity': 'rare',
                'level': 1,
                'strength': 3,
                'intelligence': 8,
                'constitution': 4,
                'dexterity': 7,
                'charisma': 3,
                'abilities': 'Cunning - Plans and executes complex schemes. Resentment - Driven by bitterness and desire for recognition. Manipulation - Influences others through subtle means.',
                'order': 5,
            },
            {
                'name': 'Grushenka',
                'slug': 'grushenka',
                'description': 'A beautiful and enigmatic woman who becomes the object of desire for both Fyodor and Dmitri. Grushenka is complex, capable of both manipulation and genuine love, representing the power of feminine influence.',
                'card_type': 'character',
                'rarity': 'epic',
                'level': 1,
                'strength': 3,
                'intelligence': 7,
                'constitution': 5,
                'dexterity': 6,
                'charisma': 9,
                'abilities': 'Allure - Captivates and influences men through charm. Independence - Makes her own choices despite societal expectations. Transformation - Capable of genuine change and growth.',
                'order': 6,
            },
            {
                'name': 'Katerina Ivanovna',
                'slug': 'katerina-ivanovna',
                'description': 'Dmitri\'s proud and noble fiancée. Katerina is intelligent, strong-willed, and driven by a sense of honor and duty. Her relationship with Dmitri is marked by pride, love, and ultimately, sacrifice.',
                'card_type': 'character',
                'rarity': 'rare',
                'level': 1,
                'strength': 4,
                'intelligence': 8,
                'constitution': 6,
                'dexterity': 5,
                'charisma': 7,
                'abilities': 'Nobility - Acts with honor and dignity. Pride - Maintains self-respect despite challenges. Sacrifice - Willing to endure for others.',
                'order': 7,
            },
            {
                'name': 'Father Zosima',
                'slug': 'father-zosima',
                'description': 'Alyosha\'s spiritual mentor, an elder monk known for his wisdom, compassion, and profound understanding of human nature. Zosima\'s teachings and example guide Alyosha and influence the novel\'s spiritual themes.',
                'card_type': 'character',
                'rarity': 'legendary',
                'level': 1,
                'strength': 3,
                'intelligence': 9,
                'constitution': 5,
                'dexterity': 4,
                'charisma': 9,
                'abilities': 'Wisdom - Deep understanding of human nature and spirituality. Teaching - Guides others toward enlightenment. Compassion - Shows unconditional love and forgiveness.',
                'order': 8,
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



