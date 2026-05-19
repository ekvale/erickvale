from __future__ import annotations

from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .agents import LEADERS, leader_by_id
from .authz import is_mdh_briefings_owner, mdh_briefings_configured
from .briefing_store import briefing_to_card_context, save_briefing
from .models import LeaderBriefing
from . import services

_PRIVATE_HEADERS = {
    'X-Robots-Tag': 'noindex, nofollow',
    'Cache-Control': 'private, no-store',
}


def _apply_private_headers(response):
    for key, value in _PRIVATE_HEADERS.items():
        response[key] = value
    return response


def _require_owner(request):
    if not mdh_briefings_configured():
        raise PermissionDenied(
            'MDH briefings are not configured (set MDH_BRIEFINGS_OWNER_USERNAME or ID).'
        )
    if not is_mdh_briefings_owner(request.user):
        raise PermissionDenied()


def _today() -> date:
    return timezone.localdate()


@login_required
@require_GET
def dashboard(request):
    _require_owner(request)
    today = _today()
    leaders_ctx = []
    for leader in LEADERS:
        has_briefing = LeaderBriefing.objects.filter(
            leader_id=leader['id'],
            date=today,
        ).exists()
        leaders_ctx.append({**leader, 'has_briefing': has_briefing})
    response = render(
        request,
        'mdh_briefings/dashboard.html',
        {
            'leaders': leaders_ctx,
            'today': today,
        },
    )
    return _apply_private_headers(response)


@login_required
@require_POST
def generate_briefing(request, leader_id: str):
    _require_owner(request)
    leader = leader_by_id(leader_id)
    if not leader:
        return _apply_private_headers(HttpResponse('Leader not found.', status=404))

    today = _today()
    existing = LeaderBriefing.objects.filter(leader_id=leader_id, date=today).first()
    if existing:
        ctx = briefing_to_card_context(existing)
        return _apply_private_headers(
            render(request, 'mdh_briefings/briefing_card.html', ctx)
        )

    try:
        data = services.generate_briefing(leader, today)
        briefing = save_briefing(leader, today, data)
        ctx = briefing_to_card_context(briefing)
        ctx['cached'] = False
        return _apply_private_headers(
            render(request, 'mdh_briefings/briefing_card.html', ctx)
        )
    except Exception as exc:
        logger_msg = str(exc) or exc.__class__.__name__
        return _apply_private_headers(
            render(
                request,
                'mdh_briefings/briefing_card.html',
                {
                    'leader_id': leader_id,
                    'error': logger_msg,
                    'schedule': [],
                    'core_beliefs': '',
                    'vision': '',
                'top_priorities': [],
                'relevant_news': [],
                'high_value_projects': [],
                'cached': False,
            },
        )
        )


@login_required
@require_POST
def generate_all(request):
    _require_owner(request)
    today = _today()
    for leader in LEADERS:
        if LeaderBriefing.objects.filter(leader_id=leader['id'], date=today).exists():
            continue
        try:
            data = services.generate_briefing(leader, today)
            save_briefing(leader, today, data)
        except Exception:
            continue
    count = LeaderBriefing.objects.filter(date=today).count()
    return _apply_private_headers(JsonResponse({'status': 'ok', 'count': count}))
