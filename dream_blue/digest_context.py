"""Build template context for the Dream Blue biweekly / operations report (calendar, KPIs, GrantScout)."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from .models import (
    BusinessCalendarEvent,
    BusinessCalendarEventType,
    BusinessKPIEntry,
    BusinessReportSection,
    GrantScoutRun,
    GrantScoutRunStatus,
)


def get_latest_completed_grantscout_run():
    return (
        GrantScoutRun.objects.filter(status=GrantScoutRunStatus.COMPLETED)
        .order_by('-created_at')
        .first()
    )


def top_grantscout_opportunities(run: GrantScoutRun, limit: int = 15):
    return list(
        run.opportunities.order_by('-priority_score', '-created_at')[:limit]
    )


def _calendar_lookahead_days() -> int:
    try:
        return max(1, int(getattr(settings, 'DREAM_BLUE_CALENDAR_LOOKAHEAD_DAYS', 120)))
    except (TypeError, ValueError):
        return 120


def upcoming_business_calendar_events():
    """Dates in the lookahead window: primary due date **or** range end (e.g. lease end)."""
    today = timezone.localdate()
    end = today + timedelta(days=_calendar_lookahead_days())
    return list(
        BusinessCalendarEvent.objects.filter(is_active=True)
        .filter(
            Q(due_date__gte=today, due_date__lte=end)
            | Q(end_date__gte=today, end_date__lte=end)
        )
        .distinct()
        .order_by('due_date', 'sort_order', 'id')
    )


def active_lease_schedule():
    """Non-expired lease rows for roster (start/end, rent, deposits in notes)."""
    today = timezone.localdate()
    return list(
        BusinessCalendarEvent.objects.filter(
            is_active=True,
            event_type=BusinessCalendarEventType.LEASE,
        )
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
        .order_by('sort_order', 'property_label', 'due_date', 'id')
    )


def build_operations_calendar_markdown() -> str:
    """Markdown appendix for GrantScout compiled_report: leases + upcoming milestones."""
    lines = [
        '## Business calendar and leases',
        '',
        '### Active leases',
        '',
        '| Property | Tenant | Start | End | Rent/mo | Deposits / notes |',
        '| --- | --- | --- | --- | ---: | --- |',
    ]
    leases = active_lease_schedule()
    if not leases:
        lines.append('_No active leases in schedule._')
    else:
        for row in leases:
            start = row.due_date.isoformat() if row.due_date else ''
            lend = row.end_date.isoformat() if row.end_date else ''
            rent = ''
            if row.amount is not None:
                rent = (
                    f'${row.amount:,.0f}'
                    if row.amount == int(row.amount)
                    else f'${row.amount:.2f}'
                )
            notes = (row.notes or '').replace('|', '\\|').replace('\n', ' ')
            tenant = (row.title or '').replace('|', '\\|')
            prop = (row.property_label or '').replace('|', '\\|')
            lines.append(
                f'| {prop} | {tenant} | {start} | {lend} | {rent} | {notes} |'
            )

    lines.extend(['', '### Upcoming milestones (next window)', ''])
    upcoming = upcoming_business_calendar_events()
    if not upcoming:
        lines.append('_No events in the current digest window._')
    else:
        for e in upcoming:
            dd = e.due_date.isoformat() if e.due_date else ''
            ed = e.end_date.isoformat() if e.end_date else ''
            rng = f'{dd}' + (f' – {ed}' if ed else '')
            amt = ''
            if e.amount is not None:
                amt = (
                    f' (${e.amount:,.0f})'
                    if e.amount == int(e.amount)
                    else f' (${e.amount:.2f})'
                )
            lines.append(
                f'- **{rng}** · {e.get_event_type_display()} · {e.title}{amt}'
            )

    return '\n'.join(lines).strip()


def active_business_kpis():
    return list(
        BusinessKPIEntry.objects.filter(is_active=True).order_by('sort_order', 'id')
    )


def active_business_report_sections():
    """Narrative blocks (manual or future KPI/BI agent)."""
    return list(
        BusinessReportSection.objects.filter(is_active=True).order_by(
            'sort_order', 'slug'
        )
    )


def build_monthly_digest_context(*, include_grantscout: bool = True) -> dict:
    now = timezone.now()
    today = timezone.localdate()
    window_end = today + timedelta(days=_calendar_lookahead_days())
    ctx = {
        'generated_at': now,
        'title': 'Dream Blue report',
        'report_subtitle': 'Operations, KPIs, and GrantScout',
        'calendar_window_start': today,
        'calendar_window_end': window_end,
        'business_calendar_events': upcoming_business_calendar_events(),
        'business_lease_schedule': active_lease_schedule(),
        'business_kpis': active_business_kpis(),
        'business_report_sections': active_business_report_sections(),
        'grantscout_run': None,
        'grantscout_opportunities': [],
        'grantscout_drift': [],
    }
    if not include_grantscout:
        return ctx
    run = get_latest_completed_grantscout_run()
    if not run:
        return ctx
    ctx['grantscout_run'] = run
    ctx['grantscout_opportunities'] = top_grantscout_opportunities(run)
    ctx['grantscout_opportunities_unverified'] = list(
        run.opportunities.filter(source_url_check_passed=False).order_by(
            '-priority_score', '-created_at'
        )[:25]
    )
    ctx['grantscout_drift'] = list(run.drift_entries.all()[:50])
    return ctx
