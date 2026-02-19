"""
Backfill occupation for existing suspects (added in 0002).
Usage: python manage.py backfill_occupations
"""
import random
from django.core.management.base import BaseCommand
from arm_chair_detective.models import Suspect, SuspectAttributeChoices


class Command(BaseCommand):
    help = 'Backfill occupation for suspects who have occupation=unknown'

    def handle(self, *args, **options):
        occupations = [c[0] for c in SuspectAttributeChoices.OCCUPATIONS if c[0] != 'unknown']
        total = 0
        batch_size = 5000
        while True:
            suspects = list(Suspect.objects.filter(occupation='unknown')[:batch_size])
            if not suspects:
                break
            for s in suspects:
                s.occupation = random.choice(occupations)
            Suspect.objects.bulk_update(suspects, ['occupation'], batch_size=batch_size)
            total += len(suspects)
            self.stdout.write(f'  Updated {total}...')
        self.stdout.write(self.style.SUCCESS(f'Done. Updated {total} suspects.'))
