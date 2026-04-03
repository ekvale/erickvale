from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string

from dream_blue.digest_context import build_monthly_digest_context
from dream_blue.emailing import (
    DreamBlueEmailConfigError,
    get_digest_recipients,
    send_html_digest,
)


class Command(BaseCommand):
    help = (
        'Send the Dream Blue HTML digest to DREAM_BLUE_REPORT_RECIPIENTS '
        '(Resend or SMTP via settings).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print recipient count and exit without sending.',
        )
        parser.add_argument(
            '--no-grantscout',
            action='store_true',
            help='Omit GrantScout section from the email body.',
        )
        parser.add_argument(
            '--subject',
            type=str,
            default='',
            help='Override email subject (default: Dream Blue digest + month/year).',
        )

    def handle(self, *args, **options):
        recipients = get_digest_recipients()
        if not recipients:
            raise CommandError(
                'DREAM_BLUE_REPORT_RECIPIENTS is empty or unset; no recipients to send to.'
            )

        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f'Dry run: would send to {len(recipients)} recipient(s).')
            )
            return

        include_gs = not options['no_grantscout']
        context = build_monthly_digest_context(include_grantscout=include_gs)
        if options['subject']:
            subject = options['subject']
        else:
            subject = f"Dream Blue digest — {datetime.now().strftime('%B %Y')}"

        html = render_to_string('dream_blue/emails/monthly_digest.html', context)

        try:
            send_html_digest(subject, html, recipients=recipients)
        except DreamBlueEmailConfigError as e:
            raise CommandError(str(e)) from e

        self.stdout.write(
            self.style.SUCCESS(f'Sent digest "{subject}" to {len(recipients)} recipient(s).')
        )
