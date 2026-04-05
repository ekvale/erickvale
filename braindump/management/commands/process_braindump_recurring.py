from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from braindump.authz import braindump_configured
from braindump.email_common import get_braindump_owner
from braindump.recurring_spawn import process_recurring_captures_for_owner


class Command(BaseCommand):
    help = (
        'Create captures from due RecurringCaptureRule rows (same logic as the morning digest). '
        'Optional cron before or instead of digest, e.g.: '
        '25 5 * * * cd /path/to/erickvale && venv/bin/python manage.py process_braindump_recurring'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            metavar='YYYY-MM-DD',
            help='Treat "today" as this date (testing).',
        )

    def handle(self, *args, **options):
        if not braindump_configured():
            raise CommandError(
                'Set BRAINDUMP_OWNER_USERNAME or BRAINDUMP_OWNER_USER_ID in settings / env.'
            )
        owner = get_braindump_owner()
        if not owner:
            raise CommandError('Brain dump owner user not found in database.')

        as_of = timezone.localdate()
        raw = (options.get('date') or '').strip()
        if raw:
            from datetime import datetime as dt

            try:
                as_of = dt.strptime(raw, '%Y-%m-%d').date()
            except ValueError as e:
                raise CommandError('--date must be YYYY-MM-DD') from e

        n = process_recurring_captures_for_owner(owner, as_of)
        self.stdout.write(self.style.SUCCESS(f'Processed {n} recurring rule(s) for {as_of}.'))
