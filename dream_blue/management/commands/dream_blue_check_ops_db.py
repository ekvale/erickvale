"""Diagnose missing Dream Blue operations tables (admin KPI / calendar / sections)."""

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

# Created by dream_blue.0004_business_calendar_kpi_report_sections
_EXPECTED_TABLES = (
    'dream_blue_businesscalendarevent',
    'dream_blue_businesskpientry',
    'dream_blue_businessreportsection',
)


class Command(BaseCommand):
    help = (
        'Show dream_blue migration status and verify operations tables exist. '
        'If Business KPIs in admin returns 500, run migrate then this command again.'
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Migrations for dream_blue:'))
        call_command('showmigrations', 'dream_blue', stdout=self.stdout)

        names = set(connection.introspection.table_names())
        missing = [t for t in _EXPECTED_TABLES if t not in names]
        if missing:
            self.stdout.write(
                self.style.ERROR(
                    'Missing table(s): ' + ', '.join(missing) + '. '
                    'Apply migrations on this host/database: '
                    'python manage.py migrate dream_blue'
                )
            )
            return

        self.stdout.write(self.style.SUCCESS('Operations tables are present.'))

        from django.db import DatabaseError

        from dream_blue.models import BusinessKPIEntry

        try:
            n = BusinessKPIEntry.objects.count()
        except DatabaseError as exc:
            self.stdout.write(
                self.style.ERROR(
                    f'Could not query BusinessKPIEntry (permissions or DB error): {exc}'
                )
            )
            return

        self.stdout.write(self.style.SUCCESS(f'BusinessKPIEntry.objects.count() = {n}'))
