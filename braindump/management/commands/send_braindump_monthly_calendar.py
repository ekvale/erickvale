import calendar
import logging
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from braindump.authz import braindump_configured
from braindump.calendar_build import build_month_calendar_context
from braindump.models import CaptureItem
from dream_blue.emailing import (
    DreamBlueEmailConfigError,
    parse_recipient_list,
    send_html_digest,
)

logger = logging.getLogger(__name__)


def _owner_user():
    from django.conf import settings

    User = get_user_model()
    raw_id = getattr(settings, 'BRAINDUMP_OWNER_USER_ID', None)
    if raw_id is not None and str(raw_id).strip() != '':
        try:
            return User.objects.get(pk=int(str(raw_id).strip()))
        except (User.DoesNotExist, ValueError, TypeError):
            return None
    name = (getattr(settings, 'BRAINDUMP_OWNER_USERNAME', '') or '').strip()
    if name:
        return User.objects.filter(username=name).first()
    return None


def _recipients_for(owner) -> list[str]:
    from django.conf import settings

    raw = (getattr(settings, 'BRAINDUMP_CALENDAR_EMAIL_RECIPIENTS', '') or '').strip()
    if raw:
        return parse_recipient_list(raw)
    if owner.email:
        return [owner.email.strip()]
    return []


class Command(BaseCommand):
    help = (
        'Email the brain dump owner an HTML monthly calendar: hard (time-specific) '
        'dates on the grid; soft-dated and undated captures for that month in lists below.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, default=0)
        parser.add_argument('--month', type=int, default=0)
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print recipient and counts; do not send.',
        )
        parser.add_argument(
            '--output-html',
            metavar='PATH',
            help='Write rendered HTML to this file and exit (no email).',
        )

    def handle(self, *args, **options):
        if not braindump_configured():
            raise CommandError(
                'Set BRAINDUMP_OWNER_USERNAME or BRAINDUMP_OWNER_USER_ID in settings / env.'
            )
        owner = _owner_user()
        if not owner:
            raise CommandError('Brain dump owner user not found in database.')

        today = timezone.localdate()
        y = int(options['year'] or today.year)
        m = int(options['month'] or today.month)
        if not (1 <= m <= 12):
            raise CommandError('Month must be 1–12.')

        qs = CaptureItem.objects.filter(user=owner).filter(
            Q(calendar_date__year=y, calendar_date__month=m)
            | Q(
                calendar_date__isnull=True,
                created_at__year=y,
                created_at__month=m,
            )
        )

        ctx = build_month_calendar_context(year=y, month=m, qs=qs)
        ctx['month_name'] = calendar.month_name[m]
        html = render_to_string('braindump/emails/monthly_calendar.html', ctx)

        recipients = _recipients_for(owner)
        subject = f'Brain dump calendar — {calendar.month_name[m]} {y}'

        out_path = (options.get('output_html') or '').strip()
        if out_path:
            path = Path(out_path)
            path.write_text(html, encoding='utf-8')
            self.stdout.write(
                self.style.SUCCESS(
                    f'Wrote HTML ({len(html)} bytes) to {path.resolve()}'
                )
            )
            return

        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Dry run: subject "{subject}"; items in query: {qs.count()}'
                )
            )
            if recipients:
                self.stdout.write('Recipients: ' + ', '.join(recipients))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        'No recipients (set BRAINDUMP_CALENDAR_EMAIL_RECIPIENTS or owner email) '
                        '— real send would fail.'
                    )
                )
            return

        if not recipients:
            raise CommandError(
                'No recipients: set BRAINDUMP_CALENDAR_EMAIL_RECIPIENTS or the owner user email.'
            )

        try:
            send_html_digest(subject, html, recipients=recipients)
        except DreamBlueEmailConfigError as e:
            raise CommandError(str(e)) from e

        logger.info(
            'send_braindump_monthly_calendar sent',
            extra={
                'year': y,
                'month': m,
                'recipient_count': len(recipients),
                'item_count': qs.count(),
            },
        )
        self.stdout.write(self.style.SUCCESS(f'Sent "{subject}" to {len(recipients)} recipient(s).'))
