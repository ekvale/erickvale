from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from .ai_categorize import categorize_capture_item
from .authz import braindump_configured, is_braindump_owner
from .gtd_partition import partition_active_items
from .models import CaptureItem, CaptureStatus, TaskPriority
from .morning_digest import run_morning_digest_send

# Avoid huge pastes firing hundreds of LLM calls in one request.
_MAX_CAPTURE_PARTS = 100


def _split_capture_body(raw: str) -> list[str]:
    """One item per semicolon-separated segment (GTD batch capture)."""
    parts = [p.strip() for p in raw.split(';')]
    return [p for p in parts if p][: _MAX_CAPTURE_PARTS]


def _require_owner(request):
    if not braindump_configured():
        raise PermissionDenied('Brain dump is not configured (set BRAINDUMP_OWNER_USERNAME or ID).')
    if not is_braindump_owner(request.user):
        raise PermissionDenied()


_PRIORITY_ORDER = {
    TaskPriority.URGENT: 0,
    TaskPriority.HIGH: 1,
    TaskPriority.NORMAL: 2,
    TaskPriority.LOW: 3,
}


def _prio_rank(x: CaptureItem) -> int:
    return _PRIORITY_ORDER.get(x.priority, 2)


def _sort_calendar(items: list[CaptureItem]) -> list[CaptureItem]:
    return sorted(
        items,
        key=lambda x: (
            x.calendar_date or date.max,
            _prio_rank(x),
            -x.created_at.timestamp(),
        ),
    )


def _sort_by_priority_then_created(items: list[CaptureItem]) -> list[CaptureItem]:
    return sorted(
        items,
        key=lambda x: (_prio_rank(x), -x.created_at.timestamp()),
    )


@login_required
@require_GET
def dashboard(request):
    _require_owner(request)
    active = list(
        CaptureItem.objects.filter(user=request.user, archived=False).order_by('-created_at')
    )
    parts = partition_active_items(active)
    gtd = {
        'unclear': _sort_by_priority_then_created(parts['unclear']),
        'trash_list': _sort_by_priority_then_created(parts['trash_list']),
        'reference': _sort_by_priority_then_created(parts['reference']),
        'someday': _sort_by_priority_then_created(parts['someday']),
        'calendar_hard': _sort_calendar(parts['calendar_hard']),
        'waiting': _sort_by_priority_then_created(parts['waiting']),
        'projects': _sort_by_priority_then_created(parts['projects']),
        'next_actions': _sort_by_priority_then_created(parts['next_actions']),
    }
    done_recent = list(
        CaptureItem.objects.filter(user=request.user, archived=True).order_by(
            '-completed_at'
        )[:40]
    )
    return render(
        request,
        'braindump/dashboard.html',
        {
            'gtd': gtd,
            'done_recent': done_recent,
            'status_choices': CaptureStatus.choices,
            'task_priority_choices': TaskPriority.choices,
            'max_capture_parts': _MAX_CAPTURE_PARTS,
        },
    )


@login_required
@require_http_methods(['POST'])
def morning_digest_send_now(request):
    _require_owner(request)
    result = run_morning_digest_send()
    if result['ok']:
        messages.success(request, result['message'])
    else:
        messages.error(request, result['message'])
    return HttpResponseRedirect(reverse('braindump:dashboard'))


@login_required
@require_http_methods(['POST'])
def capture_create(request):
    _require_owner(request)
    body = (request.POST.get('body') or '').strip()
    segments = _split_capture_body(body)
    if not segments:
        return HttpResponseRedirect(reverse('braindump:dashboard'))
    for chunk in segments:
        item = CaptureItem.objects.create(user=request.user, body=chunk)
        categorize_capture_item(item)
    return HttpResponseRedirect(reverse('braindump:dashboard'))


@login_required
@require_http_methods(['POST'])
def item_status(request, pk: int):
    _require_owner(request)
    item = get_object_or_404(CaptureItem, pk=pk, user=request.user)
    st = (request.POST.get('status') or '').strip()
    if st == CaptureStatus.DONE:
        item.mark_done()
    elif st == CaptureStatus.WAITING:
        item.mark_waiting(request.POST.get('waiting_for', ''))
    elif st == CaptureStatus.OPEN:
        item.mark_open()
    return HttpResponseRedirect(reverse('braindump:dashboard'))


@login_required
@require_http_methods(['POST'])
def item_calendar_date(request, pk: int):
    _require_owner(request)
    item = get_object_or_404(CaptureItem, pk=pk, user=request.user)
    raw = (request.POST.get('calendar_date') or '').strip()
    if raw:
        from datetime import datetime as dt

        try:
            item.calendar_date = dt.strptime(raw, '%Y-%m-%d').date()
        except ValueError:
            pass
    else:
        item.calendar_date = None
        item.calendar_is_hard_date = False
    hard = (request.POST.get('calendar_is_hard_date') or '').strip()
    if item.calendar_date:
        item.calendar_is_hard_date = hard in ('1', 'on', 'true', 'yes')
    else:
        item.calendar_is_hard_date = False
    item.save(
        update_fields=['calendar_date', 'calendar_is_hard_date', 'updated_at']
    )
    return HttpResponseRedirect(reverse('braindump:dashboard'))


@login_required
@require_http_methods(['POST'])
def item_update_meta(request, pk: int):
    _require_owner(request)
    item = get_object_or_404(CaptureItem, pk=pk, user=request.user)
    cat = (request.POST.get('category_label') or '').strip()[:120]
    item.category_label = cat
    pr = (request.POST.get('priority') or '').strip()
    valid = {c.value for c in TaskPriority}
    if pr in valid:
        item.priority = pr
    item.save(update_fields=['category_label', 'priority', 'updated_at'])
    return HttpResponseRedirect(reverse('braindump:dashboard'))


@login_required
@require_http_methods(['POST'])
def item_archive(request, pk: int):
    _require_owner(request)
    item = get_object_or_404(CaptureItem, pk=pk, user=request.user)
    item.archived = True
    item.save(update_fields=['archived', 'updated_at'])
    return HttpResponseRedirect(reverse('braindump:dashboard'))


@login_required
@require_http_methods(['POST'])
def recategorize(request, pk: int):
    _require_owner(request)
    item = get_object_or_404(CaptureItem, pk=pk, user=request.user)
    categorize_capture_item(item)
    return HttpResponseRedirect(reverse('braindump:dashboard'))
