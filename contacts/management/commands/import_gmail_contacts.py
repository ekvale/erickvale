from django.core.management.base import BaseCommand

from contacts.gmail_import import import_gmail_contacts


class Command(BaseCommand):
    help = 'Import contacts from Gmail sent messages (requires Gmail OAuth in settings).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max',
            type=int,
            default=500,
            help='Maximum number of sent messages to scan (default: 500).',
        )

    def handle(self, *args, **options):
        result = import_gmail_contacts(max_messages=options['max'])
        if result.error:
            self.stderr.write(self.style.ERROR(result.error))
            return
        self.stdout.write(
            self.style.SUCCESS(
                f'{result.added} contacts added, {result.skipped_existing} already existed.'
            )
        )
