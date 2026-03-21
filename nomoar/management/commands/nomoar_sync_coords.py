"""
Update latitude/longitude on HistoricalEvent rows from fixtures/initial.json
(by slug). Use when loaddata would conflict but DB rows lack coordinates.

  python manage.py nomoar_sync_coords
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from nomoar.models import HistoricalEvent


class Command(BaseCommand):
    help = 'Set lat/lng on events from nomoar/fixtures/initial.json (match by slug)'

    def handle(self, *args, **options):
        fixture_path = Path(__file__).resolve().parent.parent.parent / 'fixtures' / 'initial.json'
        if not fixture_path.exists():
            self.stderr.write(f'Missing {fixture_path}')
            return
        data = json.loads(fixture_path.read_text(encoding='utf-8'))
        updated = 0
        for row in data:
            if row.get('model') != 'nomoar.historicalevent':
                continue
            fields = row.get('fields') or {}
            slug = fields.get('slug')
            lat, lng = fields.get('latitude'), fields.get('longitude')
            if not slug or lat is None or lng is None:
                continue
            n = HistoricalEvent.objects.filter(slug=slug).update(
                latitude=float(lat),
                longitude=float(lng),
            )
            if n:
                updated += n
                self.stdout.write(f'Updated coords: {slug}')
        self.stdout.write(self.style.SUCCESS(f'Done. {updated} row(s) updated.'))
