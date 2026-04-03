"""Serialize BusinessCalendarEvent for month/year views and charts."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils.dateparse import parse_date

from .models import BusinessCalendarEvent, BusinessCalendarEventType

EVENT_TYPE_COLORS: dict[str, str] = {
    BusinessCalendarEventType.LEASE: '#1565c0',
    BusinessCalendarEventType.LOAN: '#c62828',
    BusinessCalendarEventType.UTILITY: '#2e7d32',
    BusinessCalendarEventType.PROPERTY_TAX: '#6a1b9a',
    BusinessCalendarEventType.INSURANCE: '#00838f',
    BusinessCalendarEventType.BILL: '#6d4c41',
    BusinessCalendarEventType.MAINTENANCE: '#ef6c00',
    BusinessCalendarEventType.LICENSE: '#4527a0',
    BusinessCalendarEventType.OTHER: '#455a64',
}


def events_overlapping_range(
    start: date,
    end: date,
    *,
    queryset=None,
) -> list[BusinessCalendarEvent]:
    """Inclusive window ``[start, end]``; spans, refinance_date, payoff_target_date."""
    qs = queryset if queryset is not None else BusinessCalendarEvent.objects.filter(
        is_active=True,
    )
    span = Q(due_date__lte=end) & (
        Q(end_date__isnull=True, due_date__gte=start) | Q(end_date__gte=start)
    )
    refi = (
        Q(refinance_date__isnull=False)
        & Q(refinance_date__gte=start)
        & Q(refinance_date__lte=end)
    )
    payoff = (
        Q(payoff_target_date__isnull=False)
        & Q(payoff_target_date__gte=start)
        & Q(payoff_target_date__lte=end)
    )
    return list(
        qs.filter(span | refi | payoff)
        .distinct()
        .order_by('due_date', 'sort_order', 'id')
    )


def parse_range_from_request(request) -> tuple[date, date] | None:
    """Parse GET ``start`` / ``end`` as ISO dates (FullCalendar uses end exclusive)."""
    s = (request.GET.get('start') or '').strip()
    e = (request.GET.get('end') or '').strip()
    if len(s) >= 10:
        s = s[:10]
    if len(e) >= 10:
        e = e[:10]
    ds = parse_date(s) if s else None
    de = parse_date(e) if e else None
    if not ds or not de:
        return None
    end_inclusive = de - timedelta(days=1) if de > ds else de
    return ds, end_inclusive


def serialize_events_for_json(
    events: list[BusinessCalendarEvent],
    *,
    range_start: date | None = None,
    range_end: date | None = None,
) -> list[dict]:
    """If ``range_start`` / ``range_end`` are set (inclusive), refinance and payoff milestones are only emitted when those dates fall in range."""
    out: list[dict] = []

    def _in_range(d: date) -> bool:
        if range_start is None or range_end is None:
            return True
        return range_start <= d <= range_end

    for ev in events:
        color = EVENT_TYPE_COLORS.get(ev.event_type, '#455a64')
        base = {
            'id': ev.pk,
            'title': ev.title,
            'eventType': ev.event_type,
            'eventTypeDisplay': ev.get_event_type_display(),
            'dueDate': ev.due_date.isoformat(),
            'endDate': ev.end_date.isoformat() if ev.end_date else None,
            'propertyLabel': ev.property_label or '',
            'amount': str(ev.amount) if ev.amount is not None else None,
            'notes': (ev.notes or '')[:500],
            'color': color,
            'accountReference': ev.account_reference or '',
            'contactInfo': ev.contact_info or '',
            'interestRate': str(ev.interest_rate_annual)
            if ev.interest_rate_annual is not None
            else None,
        }
        out.append(
            {
                **base,
                'kind': 'milestone',
                'label': _milestone_label(ev),
                'start': ev.due_date.isoformat(),
            }
        )
        if ev.end_date and ev.end_date > ev.due_date:
            out.append(
                {
                    **base,
                    'kind': 'range',
                    'label': f'{ev.get_event_type_display()}: {ev.title}'[:80],
                    'start': ev.due_date.isoformat(),
                    'endExclusive': (ev.end_date + timedelta(days=1)).isoformat(),
                    'background': True,
                }
            )
        if getattr(ev, 'refinance_date', None) and _in_range(ev.refinance_date):
            out.append(
                {
                    **base,
                    'kind': 'milestone',
                    'label': f'Refi: {ev.title[:56]}',
                    'start': ev.refinance_date.isoformat(),
                }
            )
        if getattr(ev, 'payoff_target_date', None) and _in_range(ev.payoff_target_date):
            lbl = f'Payoff: {ev.title[:50]}'
            if ev.payoff_balance is not None:
                lbl = f'Payoff ${ev.payoff_balance:,.0f}: {ev.title[:36]}'
            out.append(
                {
                    **base,
                    'kind': 'milestone',
                    'label': lbl[:80],
                    'start': ev.payoff_target_date.isoformat(),
                }
            )
    return out


def _milestone_label(ev: BusinessCalendarEvent) -> str:
    if ev.event_type == BusinessCalendarEventType.LEASE:
        return f'Lease: {ev.title}'
    if ev.event_type == BusinessCalendarEventType.LOAN:
        return f'Loan: {ev.title}'
    if ev.event_type == BusinessCalendarEventType.PROPERTY_TAX:
        return f'Tax: {ev.title}'
    if ev.event_type == BusinessCalendarEventType.UTILITY:
        return f'Utility: {ev.title}'
    if ev.event_type == BusinessCalendarEventType.INSURANCE:
        return f'Insurance: {ev.title}'
    if ev.event_type == BusinessCalendarEventType.BILL:
        return f'Bill: {ev.title}'
    return ev.title


def expense_by_type_summary(*, queryset=None) -> dict:
    qs = queryset if queryset is not None else BusinessCalendarEvent.objects.filter(
        is_active=True,
    )
    sums: dict[str, Decimal] = defaultdict(lambda: Decimal('0'))
    counts: dict[str, int] = defaultdict(int)
    for ev in qs:
        counts[ev.event_type] += 1
        if ev.amount is not None:
            sums[ev.event_type] += ev.amount or Decimal('0')

    choices = dict(BusinessCalendarEventType.choices)

    amt_labels: list[str] = []
    amt_values: list[float] = []
    amt_colors: list[str] = []
    for et, total in sorted(sums.items(), key=lambda x: -x[1]):
        amt_labels.append(choices.get(et, et))
        amt_values.append(float(total))
        amt_colors.append(EVENT_TYPE_COLORS.get(et, '#455a64'))

    cnt_labels: list[str] = []
    cnt_values: list[int] = []
    cnt_colors: list[str] = []
    for et, n in sorted(counts.items(), key=lambda x: -x[1]):
        cnt_labels.append(choices.get(et, et))
        cnt_values.append(n)
        cnt_colors.append(EVENT_TYPE_COLORS.get(et, '#455a64'))

    return {
        'amountByType': {
            'labels': amt_labels,
            'values': amt_values,
            'colors': amt_colors,
            'total': float(sum(amt_values)) if amt_values else 0.0,
        },
        'countByType': {
            'labels': cnt_labels,
            'values': cnt_values,
            'colors': cnt_colors,
            'total': sum(cnt_values) if cnt_values else 0,
        },
    }
