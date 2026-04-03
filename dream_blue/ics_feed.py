"""ICS (iCalendar) export for staff — operations dates (leases, loans, tax, etc.)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from datetime import timezone as dt_timezone

from django.db.models import Q
from django.utils import timezone

from .models import BusinessCalendarEvent


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


def build_operations_calendar_ics(
    *,
    lookahead_days: int = 120,
    event_types: tuple[str, ...] | None = None,
) -> bytes:
    today = timezone.localdate()
    end = today + timedelta(days=max(1, lookahead_days))
    now = timezone.now()

    qs = (
        BusinessCalendarEvent.objects.filter(is_active=True)
        .filter(
            Q(due_date__gte=today, due_date__lte=end)
            | Q(end_date__gte=today, end_date__lte=end)
            | Q(refinance_date__gte=today, refinance_date__lte=end)
            | Q(payoff_target_date__gte=today, payoff_target_date__lte=end)
        )
        .distinct()
        .order_by('due_date', 'sort_order', 'id')
    )
    if event_types:
        qs = qs.filter(event_type__in=event_types)

    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Dream Blue//Operations//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        f'DTSTAMP:{_fmt_datetime_utc(now)}',
    ]

    for ev in qs[:500]:
        uid = f'dream-blue-event-{ev.id}@erickvale'
        desc_bits = []
        if ev.property_label:
            desc_bits.append(ev.property_label)
        if ev.amount is not None:
            desc_bits.append(f'Amount: {ev.amount}')
        if ev.notes:
            desc_bits.append(ev.notes[:800])
        desc = _ics_escape(' | '.join(desc_bits))
        summary = _ics_escape(f'{ev.get_event_type_display()}: {ev.title}'[:180])
        lines.append('BEGIN:VEVENT')
        lines.append(f'UID:{uid}')
        lines.append(f'DTSTAMP:{_fmt_datetime_utc(now)}')
        lines.append(f'DTSTART;VALUE=DATE:{_fmt_date(ev.due_date)}')
        if ev.end_date and ev.end_date > ev.due_date:
            lines.append(f'DTEND;VALUE=DATE:{_fmt_date(ev.end_date + timedelta(days=1))}')
        lines.append(f'SUMMARY:{summary}')
        if desc:
            lines.append(f'DESCRIPTION:{desc}')
        lines.append('END:VEVENT')

    lines.append('END:VCALENDAR')
    return ('\r\n'.join(lines) + '\r\n').encode('utf-8')
