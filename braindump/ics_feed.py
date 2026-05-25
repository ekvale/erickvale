"""ICS (iCalendar) export for brain dump — subscribe in Google Calendar via URL."""

from __future__ import annotations

import secrets
from datetime import date, datetime, timedelta
from datetime import timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from .contact_calendar import birthday_falls_on_date, make_birthday_entry
from .email_common import get_braindump_owner
from .models import CaptureItem, CaptureStatus, PersonalContact
from .office_mdh_schedule import iter_mdh_office_days, mdh_office_time_window_label


def _ics_escape(text: str) -> str:
    return (
        text.replace('\\', '\\\\')
        .replace(';', '\\;')
        .replace(',', '\\,')
        .replace('\n', '\\n')
        .replace('\r', '')
    )


def _fmt_date(d: date) -> str:
    return d.strftime('%Y%m%d')


def _fmt_datetime_utc(dt: datetime) -> str:
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    dt = dt.astimezone(dt_timezone.utc)
    return dt.strftime('%Y%m%dT%H%M%SZ')


def _ics_timezone() -> ZoneInfo:
    """Calendar dates/times for the feed (default Central — server TIME_ZONE may be UTC)."""
    name = (getattr(settings, 'BRAINDUMP_ICS_TIMEZONE', '') or 'America/Chicago').strip()
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo('America/Chicago')


def _ics_today() -> date:
    return datetime.now(_ics_timezone()).date()


def ics_feed_authorized(request) -> bool:
    """
    Google Calendar fetches feeds without cookies — allow ``?token=`` when
    ``BRAINDUMP_ICS_SECRET`` is set, or the logged-in brain dump owner.
    """
    secret = (getattr(settings, 'BRAINDUMP_ICS_SECRET', '') or '').strip()
    if secret:
        token = (request.GET.get('token') or '').strip()
        if token and secrets.compare_digest(token, secret):
            return True
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        from .authz import is_braindump_owner

        return is_braindump_owner(user)
    return False


def resolve_ics_owner(request):
    """Items belong to the owner account; prefer the logged-in owner when applicable."""
    from .authz import is_braindump_owner

    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated and is_braindump_owner(user):
        return user
    return get_braindump_owner()


def _lookahead_days() -> int:
    try:
        return max(1, int(getattr(settings, 'BRAINDUMP_ICS_LOOKAHEAD_DAYS', 120)))
    except (TypeError, ValueError):
        return 120


def _lookback_days() -> int:
    try:
        return max(0, int(getattr(settings, 'BRAINDUMP_ICS_LOOKBACK_DAYS', 14)))
    except (TypeError, ValueError):
        return 14


def _include_office_holds(request) -> bool:
    if (request.GET.get('no_office') or '').lower() in ('1', 'true', 'yes'):
        return False
    return bool(getattr(settings, 'BRAINDUMP_MDH_OFFICE_ENABLED', True))


def _include_birthdays(request) -> bool:
    return (request.GET.get('no_birthdays') or '').lower() not in ('1', 'true', 'yes')


def _hard_dates_only(request) -> bool:
    return (request.GET.get('hard_only') or '').lower() in ('1', 'true', 'yes')


def _capture_summary(item: CaptureItem) -> str:
    label = (item.title or item.body or 'Brain dump').strip()
    if item.category_label:
        label = f'{item.category_label}: {label}'
    if item.calendar_date and not item.calendar_is_hard_date:
        label = f'[Flex] {label}'
    return label[:180]


def build_braindump_calendar_ics(
    *,
    owner,
    request,
    lookahead_days: int | None = None,
    lookback_days: int | None = None,
) -> bytes:
    today = _ics_today()
    la = lookahead_days if lookahead_days is not None else _lookahead_days()
    lb = lookback_days if lookback_days is not None else _lookback_days()
    d0 = today - timedelta(days=lb)
    d1 = today + timedelta(days=max(1, la))
    now = timezone.now()
    win = mdh_office_time_window_label()

    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Brain dump//GTD calendar//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        f'DTSTAMP:{_fmt_datetime_utc(now)}',
        'REFRESH-INTERVAL;VALUE=DURATION:PT2H',
        'X-PUBLISHED-TTL:PT2H',
        'X-WR-CALNAME:Brain dump',
        f'X-WR-TIMEZONE:{_ics_timezone().key}',
    ]

    captures = CaptureItem.objects.filter(
        user=owner,
        calendar_date__gte=d0,
        calendar_date__lte=d1,
    ).exclude(calendar_date__isnull=True)
    if _hard_dates_only(request):
        captures = captures.filter(calendar_is_hard_date=True)
    captures = captures.order_by('calendar_date', '-created_at')

    for item in captures[:500]:
        d = item.calendar_date
        uid = f'braindump-capture-{item.pk}@erickvale'
        summary = _ics_escape(_capture_summary(item))
        desc_bits = []
        if item.body and item.body != (item.title or ''):
            desc_bits.append(item.body[:800])
        if item.next_action:
            desc_bits.append(f'Next: {item.next_action[:400]}')
        if item.waiting_for:
            desc_bits.append(f'Waiting: {item.waiting_for[:200]}')
        if not item.calendar_is_hard_date:
            desc_bits.append('Soft date (next-action list); check Hard date in brain dump for landscape.')
        if item.status == CaptureStatus.DONE:
            desc_bits.append('(Done in brain dump)')
        desc = _ics_escape(' | '.join(desc_bits)) if desc_bits else ''

        lines.append('BEGIN:VEVENT')
        lines.append(f'UID:{uid}')
        lines.append(f'DTSTAMP:{_fmt_datetime_utc(now)}')
        lines.append(f'DTSTART;VALUE=DATE:{_fmt_date(d)}')
        lines.append(f'DTEND;VALUE=DATE:{_fmt_date(d + timedelta(days=1))}')
        lines.append(f'SUMMARY:{summary}')
        if desc:
            lines.append(f'DESCRIPTION:{desc}')
        if item.status == CaptureStatus.DONE:
            lines.append('TRANSP:TRANSPARENT')
        lines.append('END:VEVENT')

    if _include_office_holds(request):
        for d in iter_mdh_office_days(d0, d1):
            uid = f'braindump-mdh-office-{d.isoformat()}@erickvale'
            summary = _ics_escape(f'MDH in office ({win})')
            body = (
                f'Standing availability block (not a task), {win}. '
                'Unavailable for other daytime commitments unless noted.'
            )
            lines.append('BEGIN:VEVENT')
            lines.append(f'UID:{uid}')
            lines.append(f'DTSTAMP:{_fmt_datetime_utc(now)}')
            lines.append(f'DTSTART;VALUE=DATE:{_fmt_date(d)}')
            lines.append(f'DTEND;VALUE=DATE:{_fmt_date(d + timedelta(days=1))}')
            lines.append(f'SUMMARY:{summary}')
            lines.append(f'DESCRIPTION:{_ics_escape(body)}')
            lines.append('TRANSP:OPAQUE')
            lines.append('END:VEVENT')

    if _include_birthdays(request):
        contacts = PersonalContact.objects.filter(
            user=owner,
            birth_date__isnull=False,
        ).order_by('display_name', 'pk')
        d = d0
        while d <= d1:
            for contact in contacts:
                if not birthday_falls_on_date(contact.birth_date, d):
                    continue
                entry = make_birthday_entry(contact, d)
                uid = f'braindump-birthday-{contact.pk}-{d.isoformat()}@erickvale'
                summary = _ics_escape(entry.title[:180])
                lines.append('BEGIN:VEVENT')
                lines.append(f'UID:{uid}')
                lines.append(f'DTSTAMP:{_fmt_datetime_utc(now)}')
                lines.append(f'DTSTART;VALUE=DATE:{_fmt_date(d)}')
                lines.append(f'DTEND;VALUE=DATE:{_fmt_date(d + timedelta(days=1))}')
                lines.append(f'SUMMARY:{summary}')
                lines.append('TRANSP:TRANSPARENT')
                lines.append('END:VEVENT')
            d += timedelta(days=1)

    lines.append('END:VCALENDAR')
    return ('\r\n'.join(lines) + '\r\n').encode('utf-8')


def build_braindump_calendar_ics_for_owner(owner, request) -> bytes:
    return build_braindump_calendar_ics(owner=owner, request=request)


def build_braindump_calendar_ics_from_request(request) -> bytes | None:
    """Return ICS bytes or None if owner is not configured."""
    owner = resolve_ics_owner(request)
    if not owner:
        return None
    return build_braindump_calendar_ics_for_owner(owner, request)


def count_ics_events(body: bytes) -> int:
    return body.count(b'BEGIN:VEVENT')
