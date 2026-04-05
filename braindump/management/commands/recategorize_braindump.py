"""Re-run AI clarification + work-stream merge on existing captures."""

import time

from django.core.management.base import BaseCommand, CommandError
from django.db.models import QuerySet

from braindump.ai_categorize import categorize_capture_item
from braindump.authz import braindump_configured
from braindump.email_common import get_braindump_owner
from braindump.models import CaptureItem


class Command(BaseCommand):
    help = (
        'Re-run AI categorization (GTD fields + work stream) on existing CaptureItem rows. '
        'Uses the same pipeline as new captures: Anthropic/Perplexity per settings, then '
        'keyword rules merged with the model category field. '
        'Example: python manage.py recategorize_braindump --limit 20'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            help='Only items for this user (default: BRAINDUMP_OWNER_USERNAME / ID).',
        )
        parser.add_argument(
            '--include-archived',
            action='store_true',
            help='Also recategorize archived (done) items.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            metavar='N',
            help='Process at most N items (0 = no limit).',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.0,
            metavar='SEC',
            help='Pause SEC seconds between API calls (rate limits).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List how many items would be processed; no API calls.',
        )
        parser.add_argument(
            '--pks',
            nargs='+',
            type=int,
            metavar='PK',
            help='Only these primary keys (must belong to the target user).',
        )

    def handle(self, *args, **options):
        if not braindump_configured():
            raise CommandError(
                'Set BRAINDUMP_OWNER_USERNAME or BRAINDUMP_OWNER_USER_ID in settings / env.'
            )

        from django.contrib.auth import get_user_model

        User = get_user_model()
        uname = (options.get('username') or '').strip()
        if uname:
            user = User.objects.filter(username=uname).first()
            if not user:
                raise CommandError(f'User not found: {uname!r}')
        else:
            user = get_braindump_owner()
            if not user:
                raise CommandError('Brain dump owner user not found in database.')

        qs: QuerySet[CaptureItem] = CaptureItem.objects.filter(user=user).order_by(
            '-updated_at'
        )
        if not options['include_archived']:
            qs = qs.filter(archived=False)

        pks = options.get('pks') or []
        if pks:
            qs = qs.filter(pk__in=pks)
            missing = set(pks) - set(qs.values_list('pk', flat=True))
            if missing:
                raise CommandError(f'No capture for this user with pk in {sorted(missing)}')

        total = qs.count()
        lim = int(options['limit'] or 0)
        if lim > 0:
            qs = qs[:lim]

        to_process = list(qs)
        n = len(to_process)

        self.stdout.write(
            f'Target user: {user.username} (pk={user.pk}). '
            f'Items to process: {n}' + (f' (of {total} matching)' if n != total else '') + '.'
        )

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry run — no API calls.'))
            return

        delay = max(0.0, float(options['delay'] or 0))
        for i, item in enumerate(to_process, start=1):
            categorize_capture_item(item)
            self.stdout.write(f'  [{i}/{n}] pk={item.pk} {item.title or item.body[:50]!r}…')
            if delay and i < n:
                time.sleep(delay)

        self.stdout.write(self.style.SUCCESS(f'Finished recategorizing {n} capture(s).'))
