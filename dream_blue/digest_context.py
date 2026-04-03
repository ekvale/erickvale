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


def active_loan_schedule():
    """Loan lines with terms (rate, maturity) still relevant or open-ended."""
    today = timezone.localdate()
    return list(
        BusinessCalendarEvent.objects.filter(
            is_active=True,
            event_type=BusinessCalendarEventType.LOAN,
        )
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
        .order_by('sort_order', 'due_date', 'id')
    )


def active_utility_schedule():
    return list(
        BusinessCalendarEvent.objects.filter(
            is_active=True,
            event_type=BusinessCalendarEventType.UTILITY,
        ).order_by('sort_order', 'property_label', 'title', 'id')
    )


def insurance_and_tax_schedule():
    return list(
        BusinessCalendarEvent.objects.filter(
            is_active=True,
            event_type__in=(
                BusinessCalendarEventType.INSURANCE,
                BusinessCalendarEventType.PROPERTY_TAX,
            ),
        ).order_by('sort_order', 'title', 'id')
    )


def operating_bills_schedule():
    """Recurring bills, maintenance, licenses, misc. (excl. lease, loan, utility)."""
    return list(
        BusinessCalendarEvent.objects.filter(
            is_active=True,
            event_type__in=(
                BusinessCalendarEventType.BILL,
                BusinessCalendarEventType.MAINTENANCE,
                BusinessCalendarEventType.LICENSE,
                BusinessCalendarEventType.OTHER,
            ),
        ).order_by('sort_order', 'title', 'id')
    )


def _md_money(amount) -> str:
    if amount is None:
        return ''
    if amount == int(amount):
        return f'${amount:,.0f}'
    return f'${amount:.2f}'


def _md_row_escape(s: str) -> str:
    return (s or '').replace('|', '\\|').replace('\n', ' ')


def build_operations_calendar_markdown() -> str:
    """Markdown appendix for GrantScout compiled_report: operations + calendar window."""
    lines = [
        '## Operations — leases, loans, utilities, expenses',
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
            rent = _md_money(row.amount)
            notes = _md_row_escape(row.notes)
            tenant = _md_row_escape(row.title)
            prop = _md_row_escape(row.property_label)
            lines.append(f'| {prop} | {tenant} | {start} | {lend} | {rent} | {notes} |')

    lines.extend(
        [
            '',
            '### Loans',
            '',
            '| Loan | Property | Start | End | Rate % | Payment/mo | Account | Contact / notes |',
            '| --- | --- | --- | --- | ---: | ---: | --- | --- |',
        ]
    )
    loans = active_loan_schedule()
    if not loans:
        lines.append('_No active loans in schedule._')
    else:
        for row in loans:
            st = row.due_date.isoformat() if row.due_date else ''
            en = row.end_date.isoformat() if row.end_date else ''
            rate = f'{row.interest_rate_annual:.2f}' if row.interest_rate_annual is not None else ''
            pay = _md_money(row.amount)
            lines.append(
                f'| {_md_row_escape(row.title)} | {_md_row_escape(row.property_label)} | '
                f'{st} | {en} | {rate} | {pay} | '
                f'{_md_row_escape(row.account_reference)} | '
                f'{_md_row_escape(row.contact_info)}; {_md_row_escape(row.notes)} |'
            )

    lines.extend(
        [
            '',
            '### Utilities',
            '',
            '| Service | Property | Account | Amt/mo (est) | Contact | Notes |',
            '| --- | --- | --- | ---: | --- | --- |',
        ]
    )
    utils = active_utility_schedule()
    if not utils:
        lines.append('_No utility rows._')
    else:
        for row in utils:
            lines.append(
                f'| {_md_row_escape(row.title)} | {_md_row_escape(row.property_label)} | '
                f'{_md_row_escape(row.account_reference)} | {_md_money(row.amount)} | '
                f'{_md_row_escape(row.contact_info)} | {_md_row_escape(row.notes)} |'
            )

    lines.extend(
        [
            '',
            '### Insurance & property tax',
            '',
            '| Item | Property | Amt/mo | Contact | Notes |',
            '| --- | --- | ---: | --- | --- |',
        ]
    )
    it = insurance_and_tax_schedule()
    if not it:
        lines.append('_No rows._')
    else:
        for row in it:
            lines.append(
                f'| {_md_row_escape(row.title)} | {_md_row_escape(row.property_label)} | '
                f'{_md_money(row.amount)} | {_md_row_escape(row.contact_info)} | '
                f'{_md_row_escape(row.notes)} |'
            )

    lines.extend(
        [
            '',
            '### Other recurring (bills, maintenance)',
            '',
            '| Item | Type | Amt | Contact | Notes |',
            '| --- | --- | ---: | --- | --- |',
        ]
    )
    bills = operating_bills_schedule()
    if not bills:
        lines.append('_No rows._')
    else:
        for row in bills:
            lines.append(
                f'| {_md_row_escape(row.title)} | {row.get_event_type_display()} | '
                f'{_md_money(row.amount)} | {_md_row_escape(row.contact_info)} | '
                f'{_md_row_escape(row.notes)} |'
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
            amt = f' ({_md_money(e.amount)})' if e.amount is not None else ''
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
        'business_loan_schedule': active_loan_schedule(),
        'business_utility_schedule': active_utility_schedule(),
        'business_insurance_tax_schedule': insurance_and_tax_schedule(),
        'business_operating_bills': operating_bills_schedule(),
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
