"""
Upsert SiteStat and HistoricalEvent rows from nomoar/fixtures/initial.json
(match by key / slug). Safe when loaddata fails on PK conflicts or the DB
only has a partial seed — fixes maps that show only a few markers.

  python manage.py nomoar_seed_from_fixture
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import dateparse

from nomoar.models import ArchiveEventType, HistoricalEvent, SiteStat


def _parse_dt(s):
    if not s:
        return None
    return dateparse.parse_datetime(s)


class Command(BaseCommand):
    help = 'Upsert nomoar SiteStat + HistoricalEvent from fixtures/initial.json'

    def handle(self, *args, **options):
        fixture_path = Path(__file__).resolve().parent.parent.parent / 'fixtures' / 'initial.json'
        if not fixture_path.exists():
            self.stderr.write(self.style.ERROR(f'Missing {fixture_path}'))
            return
        data = json.loads(fixture_path.read_text(encoding='utf-8'))

        stats_done = 0
        events_created = 0
        events_updated = 0

        for row in data:
            model = row.get('model')
            fields = row.get('fields') or {}

            if model == 'nomoar.sitestat':
                key = fields.get('key')
                if not key:
                    continue
                SiteStat.objects.update_or_create(
                    key=key,
                    defaults={
                        'label': fields.get('label', ''),
                        'value': fields.get('value', ''),
                        'suffix': fields.get('suffix', ''),
                    },
                )
                stats_done += 1
                self.stdout.write(f'SiteStat: {key}')

            elif model == 'nomoar.historicalevent':
                slug = fields.get('slug')
                if not slug:
                    continue
                lat, lng = fields.get('latitude'), fields.get('longitude')
                et = fields.get('event_type') or ArchiveEventType.POLICY
                if et not in ArchiveEventType.values:
                    et = ArchiveEventType.POLICY
                defaults = {
                    'title': fields.get('title', ''),
                    'year': int(fields['year']) if fields.get('year') is not None else 0,
                    'summary': fields.get('summary', ''),
                    'body': fields.get('body', ''),
                    'location': fields.get('location', ''),
                    'state': fields.get('state', ''),
                    'event_type': et,
                    'latitude': float(lat) if lat is not None else None,
                    'longitude': float(lng) if lng is not None else None,
                    'featured': bool(fields.get('featured', False)),
                    'raised_fists': int(fields.get('raised_fists') or 0),
                }
                obj, created = HistoricalEvent.objects.update_or_create(
                    slug=slug,
                    defaults=defaults,
                )
                if created:
                    events_created += 1
                    self.stdout.write(self.style.SUCCESS(f'Created event: {slug}'))
                    ca, ua = _parse_dt(fields.get('created_at')), _parse_dt(fields.get('updated_at'))
                    if ca or ua:
                        HistoricalEvent.objects.filter(pk=obj.pk).update(
                            **{
                                k: v
                                for k, v in [('created_at', ca), ('updated_at', ua)]
                                if v is not None
                            }
                        )
                else:
                    events_updated += 1
                    self.stdout.write(f'Updated event: {slug}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. SiteStat rows touched: {stats_done}. '
                f'Events created: {events_created}, updated: {events_updated}.'
            )
        )
