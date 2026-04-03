"""Build template context for the Dream Blue biweekly / operations report (calendar, KPIs, GrantScout)."""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from .calendar_api import EVENT_TYPE_COLORS, events_overlapping_range
from .lease_economics import build_lease_economics_snapshot
from .lease_suggestions import build_lease_suggestion_rows
from .models import (
    BusinessCalendarEvent,
    BusinessCalendarEventType,
    BusinessKPIEntry,
    BusinessReportSection,
    GrantScoutRun,
    GrantScoutRunStatus,
    LeaseCompResearchRun,
)


def get_latest_completed_grantscout_run():
    return (
        GrantScoutRun.objects.filter(status=GrantScoutRunStatus.COMPLETED)
        .order_by('-created_at')
        .first()
    )


def get_latest_completed_lease_comp_run():
    return (
        LeaseCompResearchRun.objects.filter(status=GrantScoutRunStatus.COMPLETED)
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
            | Q(refinance_date__gte=today, refinance_date__lte=end)
            | Q(payoff_target_date__gte=today, payoff_target_date__lte=end)
        )
        .distinct()
        .order_by('due_date', 'sort_order', 'id')
    )


_EMAIL_EVENT_TYPE_ABBR = {
    BusinessCalendarEventType.LEASE: 'Ls',
    BusinessCalendarEventType.LOAN: 'Ln',
    BusinessCalendarEventType.UTILITY: 'Ut',
    BusinessCalendarEventType.PROPERTY_TAX: 'Tx',
    BusinessCalendarEventType.INSURANCE: 'In',
    BusinessCalendarEventType.BILL: 'Bl',
    BusinessCalendarEventType.MAINTENANCE: 'Mn',
    BusinessCalendarEventType.LICENSE: 'Lc',
    BusinessCalendarEventType.OTHER: '·',
}


def _email_chips_for_day(
    evs: list[BusinessCalendarEvent],
    d: date,
    *,
    max_chips: int = 12,
) -> list[dict]:
    """Labels for **due/start**, **end**, **refinance_date**, **payoff_target_date**."""
    chips: list[dict] = []
    for ev in evs:
        ab = _EMAIL_EVENT_TYPE_ABBR.get(ev.event_type, '·')
        col = EVENT_TYPE_COLORS.get(ev.event_type, '#455a64')
        if ev.due_date == d:
            if ev.end_date and ev.end_date > ev.due_date:
                label = f'{ab} {ev.title[:22]} → {ev.end_date.strftime("%b %d, %Y")}'
            else:
                label = f'{ab} {ev.title[:30]}'
            chips.append({'text': label.strip()[:46], 'color': col})
        elif ev.end_date and ev.end_date == d and ev.due_date < d:
            label = f'{ab} Ends: {ev.title[:26]}'
            chips.append({'text': label.strip()[:46], 'color': col})
        refi = getattr(ev, 'refinance_date', None)
        if refi and refi == d:
            chips.append({'text': f'{ab} Refi: {ev.title[:28]}'.strip()[:46], 'color': col})
        ptd = getattr(ev, 'payoff_target_date', None)
        if ptd and ptd == d:
            bal = getattr(ev, 'payoff_balance', None)
            extra = f' ${bal:,.0f}' if bal is not None else ''
            chips.append(
                {'text': f'{ab} Payoff{extra}: {ev.title[:16]}'.strip()[:46], 'color': col}
            )
    return chips[:max_chips]


def _build_email_month_grid_from_events(
    year: int,
    month: int,
    evs: list[BusinessCalendarEvent],
) -> dict:
    """Sunday-first month grid; ``evs`` may cover a wider range (e.g. full year)."""
    cal = calendar.Calendar(firstweekday=6)
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        row = []
        for d in week:
            if d.month != month:
                row.append({'day': None, 'out_of_month': True, 'chips': []})
            else:
                row.append(
                    {
                        'day': d.day,
                        'out_of_month': False,
                        'chips': _email_chips_for_day(evs, d),
                    }
                )
        weeks.append(row)
    return {
        'year': year,
        'month': month,
        'month_label': calendar.month_name[month],
        'weeks': weeks,
    }


def build_email_calendar_month_grid(year: int, month: int) -> dict:
    """
    Sunday-first weeks for the given month; each day lists short labels for
    milestones and spans (leases, loans, bills, tax, etc.) for HTML email clients.
    """
    last_day = calendar.monthrange(year, month)[1]
    first = date(year, month, 1)
    last = date(year, month, last_day)
    evs = events_overlapping_range(first, last)
    return _build_email_month_grid_from_events(year, month, evs)


def build_email_calendar_year_grids(year: int) -> dict:
    """
    All twelve months for ``year``, with one DB query for events overlapping
    Jan 1–Dec 31 (lease starts/ends, loan maturity, tax installments, etc.).
    """
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    evs = events_overlapping_range(year_start, year_end)
    months = [
        _build_email_month_grid_from_events(year, m, evs) for m in range(1, 13)
    ]
    return {'year': year, 'months': months}


def _digest_operations_calendar_url(
    base_url: str,
    year: int,
    month: int,
    extra_query: dict | None = None,
) -> str:
    path = reverse('dream_blue:operations_calendar')
    query: dict = {'year': year, 'month': month}
    if extra_query:
        query.update(extra_query)
    qs = urlencode(query)
    root = base_url.rstrip('/') if base_url else ''
    return f'{root}{path}?{qs}'


def build_digest_email_calendar_bundle(*, today: date | None = None) -> dict:
    """
    One month grid for ``today`` plus prev/next month labels for email / web.
    Month stepping uses the live Operations calendar (staff login).
    """
    if today is None:
        today = timezone.localdate()
    y, m = today.year, today.month
    grid = build_email_calendar_month_grid(y, m)
    if m == 1:
        py, pm = y - 1, 12
    else:
        py, pm = y, m - 1
    if m == 12:
        ny, nm = y + 1, 1
    else:
        ny, nm = y, m + 1
    return {
        'grid': grid,
        'prev_year': py,
        'prev_month': pm,
        'prev_label': f'{calendar.month_name[pm]} {py}',
        'next_year': ny,
        'next_month': nm,
        'next_label': f'{calendar.month_name[nm]} {ny}',
        'month_title': f'{calendar.month_name[m]} {y}',
        'has_absolute_links': False,
        'prev_url': '',
        'next_url': '',
        'current_url': '',
        'full_year_url': '',
    }


def _attach_digest_calendar_absolute_urls(bundle: dict, base_url: str) -> dict:
    if not (base_url or '').strip():
        return bundle
    base = base_url.strip()
    gy, gm = bundle['grid']['year'], bundle['grid']['month']
    bundle['has_absolute_links'] = True
    bundle['prev_url'] = _digest_operations_calendar_url(
        base, bundle['prev_year'], bundle['prev_month']
    )
    bundle['next_url'] = _digest_operations_calendar_url(
        base, bundle['next_year'], bundle['next_month']
    )
    bundle['current_url'] = _digest_operations_calendar_url(base, gy, gm)
    bundle['full_year_url'] = _digest_operations_calendar_url(
        base, gy, gm, extra_query={'view': 'year'}
    )
    return bundle


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

    sug = build_lease_suggestion_rows(leases)
    if sug['show_section']:
        lines.extend(
            [
                '',
                '### Suggested asking rent (illustrative)',
                '',
                _md_row_escape(sug['footnote']),
                '',
                '| Property | Tenant | Above sf | Storage sf | Suggested/mo | Contract | Note |',
                '| --- | --- | ---: | ---: | ---: | ---: | --- |',
            ]
        )
        for r in sug['rows']:
            cm = _md_money(r['contract_monthly']) if r['has_contract'] else '—'
            lines.append(
                f"| {_md_row_escape(r['property_label'])} | {_md_row_escape(r['title'])} | "
                f"{r['above_sf'] or '—'} | {r['storage_sf'] or '—'} | "
                f"${int(r['suggested_monthly']):,} | {cm} | {_md_row_escape(r['location_note'])} |"
            )
        lines.append(
            f"| **Portfolio at suggested ask** | | | | **${int(sug['total_suggested_monthly']):,}** | | |"
        )

    lines.extend(
        [
            '',
            '### Loans',
            '',
            '| Loan | Property | Opened | Maturity | Rate % | Pmt/mo | Orig | Payoff bal | Payoff cal | Refi | Acct | Notes |',
            '| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- |',
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
            orig = _md_money(row.original_principal) if row.original_principal is not None else ''
            payb = ''
            if row.payoff_balance is not None:
                payb = _md_money(row.payoff_balance)
                if row.payoff_balance_as_of:
                    payb += f' as of {row.payoff_balance_as_of.isoformat()}'
            paycal = row.payoff_target_date.isoformat() if row.payoff_target_date else ''
            refi = row.refinance_date.isoformat() if row.refinance_date else ''
            extra_bits = [
                _md_row_escape(row.contact_info or ''),
                _md_row_escape(row.notes or ''),
            ]
            extra = '; '.join(b for b in extra_bits if b)
            lines.append(
                f'| {_md_row_escape(row.title)} | {_md_row_escape(row.property_label)} | '
                f'{st} | {en} | {rate} | {pay} | {orig} | {_md_row_escape(payb)} | {paycal} | {refi} | '
                f'{_md_row_escape(row.account_reference)} | {extra} |'
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
    lease_rows = active_lease_schedule()
    ctx = {
        'generated_at': now,
        'title': 'Dream Blue report',
        'report_subtitle': 'Operations, lease economics, suggested rents, KPIs, lease comps, GrantScout',
        'calendar_window_start': today,
        'calendar_window_end': window_end,
        'digest_base_url_configured': bool(
            (getattr(settings, 'DREAM_BLUE_DIGEST_BASE_URL', '') or '').strip()
        ),
        'digest_calendar': _attach_digest_calendar_absolute_urls(
            build_digest_email_calendar_bundle(today=today),
            getattr(settings, 'DREAM_BLUE_DIGEST_BASE_URL', '') or '',
        ),
        'business_calendar_events': upcoming_business_calendar_events(),
        'business_lease_schedule': lease_rows,
        'lease_suggestions': build_lease_suggestion_rows(lease_rows),
        'lease_economics': build_lease_economics_snapshot(),
        'business_loan_schedule': active_loan_schedule(),
        'business_utility_schedule': active_utility_schedule(),
        'business_insurance_tax_schedule': insurance_and_tax_schedule(),
        'business_operating_bills': operating_bills_schedule(),
        'business_kpis': active_business_kpis(),
        'business_report_sections': active_business_report_sections(),
        'lease_comp_research': get_latest_completed_lease_comp_run(),
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
