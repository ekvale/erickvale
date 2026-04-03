from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .digest_context import (
    get_latest_completed_grantscout_run,
    top_grantscout_opportunities,
)
from .models import GrantScoutDriftEntry, GrantScoutRun


def _staff(u):
    return u.is_authenticated and u.is_staff


@require_GET
@login_required
@user_passes_test(_staff)
def grantscout_dashboard(request):
    run = (
        GrantScoutRun.objects.order_by('-created_at').select_related('previous_run').first()
    )
    opportunities = []
    drift = []
    if run:
        opportunities = list(
            run.opportunities.order_by('-priority_score', '-created_at')[:25]
        )
        drift = list(run.drift_entries.all()[:40])
    return render(
        request,
        'dream_blue/grantscout_dashboard.html',
        {
            'run': run,
            'opportunities': opportunities,
            'drift': drift,
        },
    )


@require_GET
@login_required
@user_passes_test(_staff)
def grantscout_latest_api(request):
    run = get_latest_completed_grantscout_run()
    if not run:
        return JsonResponse(
            {'run': None, 'opportunities': [], 'drift': []},
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
                }
                for o in opps
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
