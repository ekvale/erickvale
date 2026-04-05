"""
Email the braindump owner a daily morning digest (active GTD lists).

Cron at 5:30 AM (use your server timezone; Django default TIME_ZONE is UTC):

    30 5 * * * cd /home/erickvale/erickvale && /home/erickvale/erickvale/venv/bin/python manage.py send_braindump_morning_digest >> /home/erickvale/logs/braindump_morning.log 2>&1

If you want 5:30 AM in America/Chicago, either set TIME_ZONE in Django settings or adjust the cron minute/hour for UTC offset.
"""

from django.core.management.base import BaseCommand, CommandError

from braindump.authz import braindump_configured
from braindump.morning_digest import run_morning_digest_send


class Command(BaseCommand):
    help = 'Send the brain dump morning digest email to the configured owner.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print subject and recipients only; do not send.',
        )
        parser.add_argument(
            '--output-html',
            metavar='PATH',
            help='Write rendered HTML to this file and exit (no email).',
        )
        parser.add_argument(
            '--date',
            metavar='YYYY-MM-DD',
            help='Pretend "today" is this date (for testing the template).',
        )

    def handle(self, *args, **options):
        if not braindump_configured():
            raise CommandError(
                'Set BRAINDUMP_OWNER_USERNAME or BRAINDUMP_OWNER_USER_ID in settings / env.'
            )

        today = None
        raw_date = (options.get('date') or '').strip()
        if raw_date:
            from datetime import datetime as dt

            try:
                today = dt.strptime(raw_date, '%Y-%m-%d').date()
            except ValueError as e:
                raise CommandError('--date must be YYYY-MM-DD') from e

        out = (options.get('output_html') or '').strip()
        result = run_morning_digest_send(
            dry_run=bool(options['dry_run']) and not out,
            output_html_path=out if out else None,
            today=today,
        )

        if out:
            self.stdout.write(self.style.SUCCESS(result['message']))
            return

        if result['ok']:
            self.stdout.write(self.style.SUCCESS(result['message']))
            return

        raise CommandError(result['message'])
