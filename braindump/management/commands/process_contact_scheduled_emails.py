import logging

from django.core.management.base import BaseCommand

from braindump.authz import braindump_configured
from braindump.email_common import get_braindump_owner
from braindump.contact_outbound import process_due_scheduled_contact_emails

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Send due ContactScheduledEmail rows (same outbound config as digests). '
        'Runs for all users by default; use --owner-only to limit to the braindump owner.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--owner-only',
            action='store_true',
            help='Only process rows for BRAINDUMP_OWNER user.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Max rows to process (default 100).',
        )

    def handle(self, *args, **options):
        limit = max(1, int(options['limit'] or 100))
        user = None
        if options['owner_only']:
            if not braindump_configured():
                self.stderr.write(self.style.ERROR('Brain dump owner is not configured.'))
                return
            user = get_braindump_owner()
            if not user:
                self.stderr.write(self.style.ERROR('Brain dump owner user not found.'))
                return

        result = process_due_scheduled_contact_emails(user=user, limit=limit)
        self.stdout.write(
            self.style.SUCCESS(
                f"Processed queue: sent={result['sent']} failed={result['failed']}"
            )
        )
