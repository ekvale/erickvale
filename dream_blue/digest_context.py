"""Build template context for the Dream Blue biweekly / operations report (calendar, KPIs, GrantScout)."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import (
    BusinessCalendarEvent,
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
    """Active events from today through the configured lookahead window."""
    today = timezone.localdate()
    end = today + timedelta(days=_calendar_lookahead_days())
    return list(
        BusinessCalendarEvent.objects.filter(
            is_active=True,
            due_date__gte=today,
            due_date__lte=end,
        ).order_by('due_date', 'sort_order', 'id')
    )


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
