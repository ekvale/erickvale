"""
Management command to populate the suspect pool for Arm Chair Detective.
Supports generating up to 1M+ suspects with varied attributes.
Usage: python manage.py generate_suspects --count 1000000
"""
import random
from django.core.management.base import BaseCommand
from django.db import transaction

from arm_chair_detective.models import Suspect, SuspectAttributeChoices

# Large name lists for variety (subset - in production you could load from file)
FIRST_NAMES_M = [
    'James', 'John', 'Robert', 'Michael', 'David', 'William', 'Richard', 'Joseph',
    'Thomas', 'Charles', 'Christopher', 'Daniel', 'Matthew', 'Anthony', 'Mark',
    'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua', 'Kenneth', 'Kevin', 'Brian',
    'George', 'Timothy', 'Ronald', 'Edward', 'Jason', 'Jeffrey', 'Jacob',
    'Gary', 'Nicholas', 'Eric', 'Jonathan', 'Stephen', 'Larry', 'Justin',
    'Scott', 'Brandon', 'Benjamin', 'Samuel', 'Raymond', 'Gregory', 'Frank',
]
FIRST_NAMES_F = [
    'Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan',
    'Jessica', 'Sarah', 'Karen', 'Lisa', 'Nancy', 'Betty', 'Margaret', 'Sandra',
    'Ashley', 'Kimberly', 'Emily', 'Donna', 'Michelle', 'Dorothy', 'Carol',
    'Amanda', 'Melissa', 'Deborah', 'Stephanie', 'Rebecca', 'Sharon', 'Laura',
    'Cynthia', 'Kathleen', 'Amy', 'Angela', 'Shirley', 'Anna', 'Brenda',
    'Pamela', 'Emma', 'Nicole', 'Helen', 'Samantha', 'Katherine', 'Christine',
]
LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
    'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
    'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
    'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark',
    'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen', 'King',
    'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores', 'Green',
    'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
    'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz',
]


def _pick(choices):
    """Pick one value from Django-style choices [(value, label), ...]."""
    if not choices:
        return None
    items = [c[0] for c in choices]
    return random.choice(items)


def create_suspect(seed=None):
    """Create a single Suspect with random attributes. Seed for reproducibility."""
    if seed is not None:
        random.seed(seed)
    gender = random.choice(['M', 'F'])
    first = random.choice(FIRST_NAMES_M if gender == 'M' else FIRST_NAMES_F)
    last = random.choice(LAST_NAMES)
    return Suspect(
        first_name=first,
        last_name=last,
        gender=gender,
        age_range=_pick(SuspectAttributeChoices.AGE_RANGES),
        hair_color=_pick(SuspectAttributeChoices.HAIR_COLORS),
        eye_color=_pick(SuspectAttributeChoices.EYE_COLORS),
        skin_tone=_pick(SuspectAttributeChoices.SKIN_TONES),
        build=_pick(SuspectAttributeChoices.BUILDS),
        height_range=_pick(SuspectAttributeChoices.HEIGHT_RANGES),
        accent_region=_pick(SuspectAttributeChoices.ACCENT_REGIONS),
        vehicle_type=_pick(SuspectAttributeChoices.VEHICLE_TYPES),
        vehicle_color=_pick(SuspectAttributeChoices.VEHICLE_COLORS),
    )


class Command(BaseCommand):
    help = 'Generate suspect pool for Arm Chair Detective (up to 1M+ suspects)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100_000,
            help='Number of suspects to generate (default: 100,000)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing suspects before generating (use with care!)',
        )
        parser.add_argument(
            '--batch',
            type=int,
            default=5000,
            help='Batch size for bulk_create (default: 5000)',
        )
        parser.add_argument(
            '--seed',
            type=int,
            default=None,
            help='Random seed for reproducible generation',
        )

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']
        batch_size = min(options['batch'], 10000)
        seed = options.get('seed')

        if count < 1:
            self.stdout.write(self.style.ERROR('Count must be >= 1'))
            return

        if clear:
            deleted, _ = Suspect.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Cleared {deleted} existing suspects.'))

        existing = Suspect.objects.count()
        target = existing + count
        self.stdout.write(f'Generating up to {count} suspects (target total: {target})...')

        created = 0
        base_seed = seed if seed is not None else random.randint(0, 2**31 - 1)

        while created < count:
            batch = min(batch_size, count - created)
            suspects = []
            for i in range(batch):
                s = create_suspect(seed=base_seed + created + i if seed is not None else None)
                suspects.append(s)
                created += 1
            Suspect.objects.bulk_create(suspects)
            self.stdout.write(f'  Created {created}/{count} suspects...')

        self.stdout.write(self.style.SUCCESS(f'Done. Total suspects: {Suspect.objects.count()}'))
