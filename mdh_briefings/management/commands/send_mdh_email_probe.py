"""
Test MDH digest email delivery (no Perplexity, no briefing generation).

  python manage.py send_mdh_email_probe
  python manage.py send_mdh_email_probe --check-only
"""

from django.core.management.base import BaseCommand, CommandError

from mdh_briefings.email_probe import run_email_probe


class Command(BaseCommand):
    help = 'Diagnose and optionally send a one-line test email to MDH_BRIEFINGS_DIGEST_RECIPIENTS.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Print configuration only; do not send.',
        )

    def handle(self, *args, **options):
        result = run_email_probe(send=not options['check_only'])

        self.stdout.write('MDH digest email probe')
        self.stdout.write(f"  raw MDH_BRIEFINGS_DIGEST_RECIPIENTS: {result.get('raw_setting')!r}")
        self.stdout.write(f"  parsed recipients: {result.get('recipients')}")
        self.stdout.write(f"  PERPLEXITY_API_KEY set: {result.get('perplexity_configured')}")
        cfg = result.get('delivery_config') or {}
        self.stdout.write(f"  resend configured: {cfg.get('resend_configured')} (from={cfg.get('resend_from')!r})")
        self.stdout.write(f"  smtp configured: {cfg.get('smtp_configured')} (host={cfg.get('smtp_host')!r})")

        if result.get('send_result'):
            self.stdout.write(f"  send_result: {result['send_result']}")

        if result['ok']:
            self.stdout.write(self.style.SUCCESS(result['message']))
            if 'resend' in str(result.get('message', '')):
                self.stdout.write(
                    '  Tip: In Resend dashboard → Emails, confirm status is "delivered" not '
                    '"bounced". @state.mn.us may block external senders even when Resend accepts.'
                )
            return

        raise CommandError(result['message'])
