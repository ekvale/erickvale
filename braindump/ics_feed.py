"""ICS (iCalendar) export for brain dump — subscribe in Google Calendar via URL."""

from __future__ import annotations

import secrets
from datetime import date, datetime, time, timedelta
from datetime import timezone as dt_timezone
from urllib.parse import unquote, unquote_plus
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


def _fold_ics_line(line: str) -> list[str]:
    """RFC 5545 §3.1 — physical lines must be ≤75 octets (Google/Outlook require this)."""
    encoded = line.encode('utf-8')
    if len(encoded) <= 75:
        return [line]
    physical: list[str] = []
    pos = 0
    first = True
    while pos < len(encoded):
        limit = 75 if first else 74
        piece = encoded[pos : pos + limit]
        while piece and (piece[-1] & 0xC0) == 0x80:
            piece = piece[:-1]
        if not piece:
            piece = encoded[pos : pos + 1]
        text = piece.decode('utf-8')
        physical.append(text if first else f' {text}')
        pos += len(piece)
        first = False
    return physical


def _emit(out: list[str], line: str) -> None:
    out.extend(_fold_ics_line(line))


def _ics_bytes(logical_lines: list[str]) -> bytes:
    physical: list[str] = []
    for line in logical_lines:
        _emit(physical, line)
    return ('\r\n'.join(physical) + '\r\n').encode('utf-8')


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


def _parse_hhmm(raw: str, *, default_h: int, default_m: int) -> tuple[int, int]:
    s = (raw or '').strip()
    if not s:
        return default_h, default_m
    parts = s.split(':', 1)
    try:
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        return max(0, min(23, h)), max(0, min(59, m))
    except (TypeError, ValueError):
        return default_h, default_m


def _mdh_office_hour_parts() -> tuple[int, int, int, int]:
    return (
        *_parse_hhmm(
            getattr(settings, 'BRAINDUMP_MDH_OFFICE_START', '08:00'),
            default_h=8,
            default_m=0,
        ),
        *_parse_hhmm(
            getattr(settings, 'BRAINDUMP_MDH_OFFICE_END', '17:00'),
            default_h=17,
            default_m=0,
        ),
    )


def _fmt_local_wall(dt: datetime) -> str:
    """Local wall time for DTSTART;TZID= (no Z suffix)."""
    return dt.strftime('%Y%m%dT%H%M%S')


def _vtimezone_lines(tz_key: str) -> list[str]:
    """VTIMEZONE blocks Google needs to interpret TZID timed events."""
    if tz_key == 'America/Chicago':
        return [
            'BEGIN:VTIMEZONE',
            'TZID:America/Chicago',
            'BEGIN:DAYLIGHT',
            'TZOFFSETFROM:-0600',
            'TZOFFSETTO:-0500',
            'TZNAME:CDT',
            'DTSTART:19700308T020000',
            'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU',
            'END:DAYLIGHT',
            'BEGIN:STANDARD',
            'TZOFFSETFROM:-0500',
            'TZOFFSETTO:-0600',
            'TZNAME:CST',
            'DTSTART:19701101T020000',
            'RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU',
            'END:STANDARD',
            'END:VTIMEZONE',
        ]
    return []


def _office_hold_datetimes(d: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    sh, sm, eh, em = _mdh_office_hour_parts()
    start = datetime.combine(d, time(sh, sm), tzinfo=tz)
    end = datetime.combine(d, time(eh, em), tzinfo=tz)
    return start, end


def _capture_timed_window(
    item: CaptureItem, d: date, tz: ZoneInfo
) -> tuple[datetime, datetime] | None:
    """Local start/end for a timed capture, or None for all-day."""
    t0 = item.calendar_time
    if not t0:
        return None
    start = datetime.combine(d, t0, tzinfo=tz)
    t1 = item.calendar_end_time
    if t1 and t1 > t0:
        end = datetime.combine(d, t1, tzinfo=tz)
    else:
        end = start + timedelta(hours=1)
    return start, end


def _ics_token_candidates(request) -> list[str]:
    """Query tokens may arrive encoded; ``+`` is often decoded as space."""
    raw = (request.GET.get('token') or request.GET.get('t') or '').strip()
    if not raw:
        return []
    out: list[str] = []
    for val in (raw, unquote(raw), unquote_plus(raw)):
        if not val:
            continue
        for cand in (val, val.replace(' ', '+')):
            if cand not in out:
                out.append(cand)
    return out


def _ics_feed_slug_from_request(request) -> str:
    match = getattr(request, 'resolver_match', None)
    if match is None:
        return ''
    return (match.kwargs.get('feed_slug') or '').strip()


def ics_feed_authorized(request) -> bool:
    """
    Google Calendar fetches feeds without cookies — allow ``?token=`` when
    ``BRAINDUMP_ICS_SECRET`` is set, ``/feed/<slug>.ics`` when
    ``BRAINDUMP_ICS_FEED_SLUG`` is set, or the logged-in brain dump owner.
    """
    slug_cfg = (getattr(settings, 'BRAINDUMP_ICS_FEED_SLUG', '') or '').strip()
    path_slug = _ics_feed_slug_from_request(request)
    if slug_cfg and path_slug and secrets.compare_digest(path_slug, slug_cfg):
        return True

    secret = (getattr(settings, 'BRAINDUMP_ICS_SECRET', '') or '').strip()
    if secret:
        for token in _ics_token_candidates(request):
            if secrets.compare_digest(token, secret):
                return True
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        from .authz import is_braindump_owner

        return is_braindump_owner(user)
    return False


def ics_feed_auth_hint(request) -> str:
    """Plain-text hint when anonymous access is denied."""
    if _ics_feed_slug_from_request(request) or _ics_token_candidates(request):
        return (
            'Invalid calendar feed credentials. Use the full subscribe URL from '
            'Brain dump → Calendar (token must be URL-encoded), or set '
            'BRAINDUMP_ICS_FEED_SLUG and use /apps/braindump/feed/<slug>.ics .'
        )
    return (
        'Brain dump calendar feed requires authentication. While logged out, use the '
        'subscribe URL from Brain dump → Calendar (?token=…, URL-encoded) or '
        '/apps/braindump/feed/<slug>.ics if BRAINDUMP_ICS_FEED_SLUG is set. '
        'Opening /calendar.ics alone always returns 403.'
    )


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


def _include_undated_captures(request) -> bool:
    if (request.GET.get('no_undated') or '').lower() in ('1', 'true', 'yes'):
        return False
    if (request.GET.get('undated') or '').lower() in ('1', 'true', 'yes'):
        return True
    return bool(getattr(settings, 'BRAINDUMP_ICS_INCLUDE_UNDATED', True))


def _capture_summary(item: CaptureItem, *, undated: bool = False) -> str:
    label = (item.title or item.body or 'Brain dump').strip()
    if item.category_label:
        label = f'{item.category_label}: {label}'
    if undated:
        label = f'[Task] {label}'
    return label[:70]


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
    tz = _ics_timezone()
    tz_key = tz.key
    include_office = _include_office_holds(request)
    vtz = _vtimezone_lines(tz_key)

    lines: list[str] = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Brain dump//GTD calendar//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        f'DTSTAMP:{_fmt_datetime_utc(now)}',
        'REFRESH-INTERVAL;VALUE=DURATION:PT2H',
        'X-PUBLISHED-TTL:PT2H',
        'X-WR-CALNAME:Brain dump',
        f'X-WR-TIMEZONE:{tz_key}',
    ]
    lines.extend(vtz)

    def _append_capture_event(item: CaptureItem, d: date, *, undated: bool = False) -> None:
        uid = f'braindump-capture-{item.pk}@erickvale'
        summary = _ics_escape(_capture_summary(item, undated=undated))
        desc_bits = []
        if undated:
            desc_bits.append('No calendar date in brain dump — shown on capture day.')
        if item.body and item.body != (item.title or ''):
            desc_bits.append(item.body[:120])
        if item.next_action:
            desc_bits.append(f'Next: {item.next_action[:80]}')
        if item.waiting_for:
            desc_bits.append(f'Waiting: {item.waiting_for[:60]}')
        if item.status == CaptureStatus.DONE:
            desc_bits.append('Done in brain dump.')
        desc = _ics_escape(' | '.join(desc_bits)[:200]) if desc_bits else ''
        timed = None if undated else _capture_timed_window(item, d, tz)

        lines.append('BEGIN:VEVENT')
        lines.append(f'UID:{uid}')
        lines.append(f'DTSTAMP:{_fmt_datetime_utc(now)}')
        lines.append('STATUS:CONFIRMED')
        if timed and vtz:
            start_dt, end_dt = timed
            lines.append(
                f'DTSTART;TZID={tz_key}:{_fmt_local_wall(start_dt)}'
            )
            lines.append(f'DTEND;TZID={tz_key}:{_fmt_local_wall(end_dt)}')
        elif timed:
            start_dt, end_dt = timed
            lines.append(f'DTSTART:{_fmt_datetime_utc(start_dt)}')
            lines.append(f'DTEND:{_fmt_datetime_utc(end_dt)}')
        else:
            lines.append(f'DTSTART;VALUE=DATE:{_fmt_date(d)}')
            lines.append(f'DTEND;VALUE=DATE:{_fmt_date(d + timedelta(days=1))}')
        lines.append(f'SUMMARY:{summary}')
        if desc:
            lines.append(f'DESCRIPTION:{desc}')
        lines.append('END:VEVENT')

    event_budget = 500
    captures = CaptureItem.objects.filter(
        user=owner,
        archived=False,
        calendar_date__gte=d0,
        calendar_date__lte=d1,
    ).exclude(calendar_date__isnull=True)
    if _hard_dates_only(request):
        captures = captures.filter(calendar_is_hard_date=True)
    captures = captures.order_by('calendar_date', '-created_at')

    for item in captures[:event_budget]:
        _append_capture_event(item, item.calendar_date)
        event_budget -= 1
        if event_budget <= 0:
            break

    if _include_undated_captures(request) and event_budget > 0:
        from .models import NonActionableDisposition

        undated = (
            CaptureItem.objects.filter(
                user=owner,
                archived=False,
                calendar_date__isnull=True,
                is_actionable=True,
            )
            .exclude(non_actionable_disposition=NonActionableDisposition.TRASH)
            .order_by('-created_at')
        )
        for item in undated[: min(event_budget, 80)]:
            created = timezone.localtime(item.created_at, tz).date()
            if created < d0 or created > d1:
                continue
            _append_capture_event(item, created, undated=True)
            event_budget -= 1
            if event_budget <= 0:
                break

    if include_office:
        for d in iter_mdh_office_days(d0, d1):
            if event_budget <= 0:
                break
            uid = f'braindump-mdh-office-{d.isoformat()}@erickvale'
            summary = _ics_escape('MDH in office')
            body = (
                f'Standing availability block (not a task), {win}. '
                'Unavailable for other daytime commitments unless noted.'
            )
            start_dt, end_dt = _office_hold_datetimes(d, tz)
            lines.append('BEGIN:VEVENT')
            lines.append(f'UID:{uid}')
            lines.append(f'DTSTAMP:{_fmt_datetime_utc(now)}')
            lines.append('STATUS:CONFIRMED')
            if vtz:
                lines.append(
                    f'DTSTART;TZID={tz_key}:{_fmt_local_wall(start_dt)}'
                )
                lines.append(f'DTEND;TZID={tz_key}:{_fmt_local_wall(end_dt)}')
            else:
                lines.append(f'DTSTART:{_fmt_datetime_utc(start_dt)}')
                lines.append(f'DTEND:{_fmt_datetime_utc(end_dt)}')
            lines.append(f'SUMMARY:{summary}')
            lines.append(f'DESCRIPTION:{_ics_escape(body)}')
            lines.append('TRANSP:OPAQUE')
            lines.append('END:VEVENT')
            event_budget -= 1

    if _include_birthdays(request):
        contacts = PersonalContact.objects.filter(
            user=owner,
            birth_date__isnull=False,
        ).order_by('display_name', 'pk')
        d = d0
        while d <= d1:
            for contact in contacts:
                if event_budget <= 0:
                    break
                if not birthday_falls_on_date(contact.birth_date, d):
                    continue
                entry = make_birthday_entry(contact, d)
                uid = f'braindump-birthday-{contact.pk}-{d.isoformat()}@erickvale'
                bday_title = entry.title.replace('\U0001f382 ', '').strip()
                summary = _ics_escape(f'Birthday: {bday_title}'[:70])
                lines.append('BEGIN:VEVENT')
                lines.append(f'UID:{uid}')
                lines.append(f'DTSTAMP:{_fmt_datetime_utc(now)}')
                lines.append('STATUS:CONFIRMED')
                lines.append(f'DTSTART;VALUE=DATE:{_fmt_date(d)}')
                lines.append(f'DTEND;VALUE=DATE:{_fmt_date(d + timedelta(days=1))}')
                lines.append(f'SUMMARY:{summary}')
                lines.append('END:VEVENT')
                event_budget -= 1
            d += timedelta(days=1)

    lines.append('END:VCALENDAR')
    return _ics_bytes(lines)


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
