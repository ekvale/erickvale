from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from .calendar_api import (
    EVENT_TYPE_COLORS,
    expense_by_type_summary,
    events_overlapping_range,
    parse_range_from_request,
    serialize_events_for_json,
)
from .digest_context import (
    get_latest_completed_grantscout_run,
    top_grantscout_opportunities,
)
from .models import (
    BusinessCalendarEventType,
    GrantScoutDriftEntry,
    GrantScoutRun,
)


def _require_staff(request):
    if not request.user.is_staff:
        raise PermissionDenied


@require_GET
@login_required
def grantscout_dashboard(request):
    _require_staff(request)
    run = (
        GrantScoutRun.objects.order_by('-created_at').select_related('previous_run').first()
    )
    opportunities = []
    drift = []
    unverified = []
    if run:
        opportunities = list(
            run.opportunities.order_by('-priority_score', '-created_at')[:25]
        )
        drift = list(run.drift_entries.all()[:40])
        unverified = list(
            run.opportunities.filter(source_url_check_passed=False).order_by(
                '-priority_score', '-created_at'
            )[:25]
        )
    return render(
        request,
        'dream_blue/grantscout_dashboard.html',
        {
            'run': run,
            'opportunities': opportunities,
            'drift': drift,
            'unverified_opportunities': unverified,
        },
    )


@require_GET
@login_required
def grantscout_latest_api(request):
    _require_staff(request)
    run = get_latest_completed_grantscout_run()
    if not run:
        return JsonResponse(
            {
                'run': None,
                'opportunities': [],
                'opportunities_unverified': [],
                'drift': [],
            },
        )
    opps = top_grantscout_opportunities(run, limit=25)
    drift_qs = GrantScoutDriftEntry.objects.filter(run=run).order_by('id')[:50]
    return JsonResponse(
        {
            'run': {
                'id': run.id,
                'period_label': run.period_label,
                'status': run.status,
                'created_at': run.created_at.isoformat(),
                'coverage_summary': run.coverage_summary,
            },
            'opportunities': [
                {
                    'id': o.id,
                    'category': o.category,
                    'category_display': o.get_category_display(),
                    'opportunity_type': o.opportunity_type,
                    'eligibility': o.eligibility,
                    'status': o.status,
                    'deadline': o.deadline.isoformat() if o.deadline else None,
                    'summary': o.summary,
                    'action_recommended': o.action_recommended,
                    'source_url': o.source_url,
                    'priority_score': o.priority_score,
                    'source_url_check_passed': o.source_url_check_passed,
                }
                for o in opps
            ],
            'opportunities_unverified': [
                {
                    'id': o.id,
                    'summary': o.summary,
                    'source_url': o.source_url,
                    'priority_score': o.priority_score,
                }
                for o in run.opportunities.filter(source_url_check_passed=False).order_by(
                    '-priority_score', '-created_at'
                )[:25]
            ],
            'drift': [
                {
                    'drift_type': d.drift_type,
                    'drift_type_display': d.get_drift_type_display(),
                    'summary': d.summary,
                    'details': d.details,
                }
                for d in drift_qs
            ],
        }
    )


@require_GET
@login_required
def operations_calendar(request):
    _require_staff(request)
    today = timezone.localdate()
    try:
        y = max(2000, min(2100, int(request.GET.get('year', today.year))))
    except (TypeError, ValueError):
        y = today.year
    try:
        m = max(1, min(12, int(request.GET.get('month', today.month))))
    except (TypeError, ValueError):
        m = today.month
    mode = (request.GET.get('view') or 'month').strip().lower()
    if mode not in ('month', 'year'):
        mode = 'month'
    return render(
        request,
        'dream_blue/operations_calendar.html',
        {
            'initial_year': y,
            'initial_month': m,
            'view_mode': mode,
            'legend': [
                (code, label, EVENT_TYPE_COLORS.get(code, '#455a64'))
                for code, label in BusinessCalendarEventType.choices
            ],
        },
    )


@require_GET
@login_required
def operations_calendar_events_api(request):
    _require_staff(request)
    parsed = parse_range_from_request(request)
    if not parsed:
        return JsonResponse(
            {'error': 'Provide start and end as ISO dates (YYYY-MM-DD).'},
            status=400,
        )
    start, end = parsed
    evs = events_overlapping_range(start, end)
    return JsonResponse(
        {
            'start': start.isoformat(),
            'end': end.isoformat(),
            'events': serialize_events_for_json(evs, range_start=start, range_end=end),
        }
    )


@require_GET
@login_required
def operations_expense_summary_api(request):
    """Totals of ``amount`` by event type (all active rows with amounts)."""
    _require_staff(request)
    return JsonResponse(expense_by_type_summary())
