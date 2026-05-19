"""
Email the daily MDH leadership priorities + news digest.

Cron (example — 6:30 AM server local time; adjust for your timezone):

    30 6 * * * cd /home/erickvale/erickvale && ./deploy/mdh_briefings_daily_digest.sh >> /home/erickvale/logs/mdh_briefings_digest.log 2>&1

Requires PERPLEXITY_API_KEY, MDH_BRIEFINGS_DIGEST_RECIPIENTS, and Resend or SMTP (same as Dream Blue digests).
"""

from datetime import datetime as dt

from django.core.management.base import BaseCommand, CommandError

from mdh_briefings.digest import run_daily_digest_send


class Command(BaseCommand):
    help = 'Send the MDH leadership daily priorities and news email digest.'

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
            help='Pretend "today" is this date (for testing).',
        )
        parser.add_argument(
            '--no-generate',
            action='store_true',
            help='Only use briefings already cached for today; do not call Perplexity for leaders.',
        )
        parser.add_argument(
            '--no-news',
            action='store_true',
            help='Omit the web news section (still sends leader priorities).',
        )

    def handle(self, *args, **options):
        today = None
        raw_date = (options.get('date') or '').strip()
        if raw_date:
            try:
                today = dt.strptime(raw_date, '%Y-%m-%d').date()
            except ValueError as e:
                raise CommandError('--date must be YYYY-MM-DD') from e

        out = (options.get('output_html') or '').strip()
        result = run_daily_digest_send(
            dry_run=bool(options['dry_run']) and not out,
            output_html_path=out if out else None,
            today=today,
            generate_missing=not options['no_generate'],
            include_news=not options['no_news'],
        )

        if out:
            self.stdout.write(self.style.SUCCESS(result['message']))
            return

        if result['ok']:
            self.stdout.write(self.style.SUCCESS(result['message']))
            return

        raise CommandError(result['message'])
