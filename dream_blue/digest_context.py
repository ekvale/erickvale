"""Build template context for monthly digest (GrantScout + placeholders for future KPIs)."""

from __future__ import annotations

from django.utils import timezone

from .models import GrantScoutOpportunity, GrantScoutRun, GrantScoutRunStatus


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


def build_monthly_digest_context(*, include_grantscout: bool = True) -> dict:
    now = timezone.now()
    ctx = {
        'generated_at': now,
        'title': 'Dream Blue monthly digest',
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
