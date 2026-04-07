import calendar as cal_mod
from datetime import date, datetime as dt

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse, QueryDict
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from .ai_categorize import categorize_capture_item
from .authz import braindump_configured, is_braindump_owner
from .dashboard_filters import (
    apply_dashboard_filters,
    filter_query_has_params,
    work_type_filter_choices,
)
from .calendar_build import build_month_calendar_context
from .gtd_partition import partition_active_items
from .models import (
    CaptureItem,
    CaptureStatus,
    EngagementChoice,
    GTDBucket,
    NonActionableDisposition,
    RecurrencePattern,
    RecurringCaptureRule,
    TaskPriority,
)
from .morning_digest import run_morning_digest_send
from .recurrence_logic import first_run_on_or_after

# Avoid huge pastes firing hundreds of LLM calls in one request.
_MAX_CAPTURE_PARTS = 100

_BRAIN_DUMP_FILTER_SESSION = 'braindump_filter_query'

_WEEKDAY_CHOICES = list(enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']))


def _dashboard_redirect(request) -> HttpResponseRedirect:
    q = request.session.get(_BRAIN_DUMP_FILTER_SESSION, '')
    base = reverse('braindump:dashboard')
    if q:
        return HttpResponseRedirect(f'{base}?{q}')
    return HttpResponseRedirect(base)


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


def _sort_date_then_priority(items: list[CaptureItem]) -> list[CaptureItem]:
    """Soonest calendar date first; undated last; then urgency; then newest created."""
    return sorted(
        items,
        key=lambda x: (
            x.calendar_date or date.max,
            _prio_rank(x),
            -x.created_at.timestamp(),
        ),
    )


def _accepts_json(request) -> bool:
    if request.POST.get('format') == 'json':
        return True
    accept = request.headers.get('Accept', '')
    return 'application/json' in accept


def _show_trash_archive_item(item: CaptureItem) -> bool:
    return (
        item.is_actionable is False
        and item.non_actionable_disposition == NonActionableDisposition.TRASH
    )


def _active_list_id(item: CaptureItem) -> str | None:
    if item.archived:
        return None
    parts = partition_active_items([item])
    for name, lst in parts.items():
        if lst:
            return name
    return None


def _item_card_html(request, item: CaptureItem, list_id: str = '') -> str:
    item.refresh_from_db()
    lid = list_id or _active_list_id(item) or ''
    return render_to_string(
        'braindump/_item_card.html',
        {
            'it': item,
            'show_trash_archive': _show_trash_archive_item(item),
            'task_priority_choices': TaskPriority.choices,
            'list_id': lid,
        },
        request=request,
    )


def _json_capture_response(
    request,
    item: CaptureItem,
    *,
    removed: bool = False,
) -> JsonResponse | None:
    if not _accepts_json(request):
        return None
    pk = item.pk
    if removed or item.archived:
        return JsonResponse({'ok': True, 'removed': True, 'pk': pk})
    item.refresh_from_db()
    if item.archived:
        return JsonResponse({'ok': True, 'removed': True, 'pk': pk})
    src = (request.POST.get('source_list') or '').strip()
    bucket = _active_list_id(item)
    bucket_changed = bool(src and bucket and src != bucket)
    if bucket_changed:
        return JsonResponse(
            {
                'ok': True,
                'removed': True,
                'pk': pk,
                'bucket_changed': True,
                'message': 'Saved. Refresh the page to see this item in its new section.',
            }
        )
    lid = src or bucket or ''
    return JsonResponse(
        {
            'ok': True,
            'removed': False,
            'pk': pk,
            'html': _item_card_html(request, item, list_id=lid),
        }
    )


def _month_bounds(y: int, m: int) -> tuple[int, int]:
    if m < 1:
        return y - 1, 12
    if m > 12:
        return y + 1, 1
    return y, m


@login_required
@require_GET
def calendar_redirect(request):
    _require_owner(request)
    t = timezone.localdate()
    return redirect('braindump:calendar_month', year=t.year, month=t.month)


@login_required
@require_GET
def calendar_month(request, year: int, month: int):
    _require_owner(request)
    if not (1 <= month <= 12) or not (2020 <= year <= 2040):
        t = timezone.localdate()
        return redirect('braindump:calendar_month', year=t.year, month=t.month)

    qs = CaptureItem.objects.filter(user=request.user).filter(
        Q(calendar_date__year=year, calendar_date__month=month)
        | Q(
            calendar_date__isnull=True,
            created_at__year=year,
            created_at__month=month,
        )
    )
    month_cal = build_month_calendar_context(
        year=year, month=month, qs=qs, calendar_user=request.user
    )
    month_cal['month_name'] = cal_mod.month_name[month]
    py, pm = _month_bounds(year, month - 1)
    ny, nm = _month_bounds(year, month + 1)
    return render(
        request,
        'braindump/calendar.html',
        {
            'month_cal': month_cal,
            'prev_year': py,
            'prev_month': pm,
            'next_year': ny,
            'next_month': nm,
        },
    )


@login_required
@require_GET
def dashboard(request):
    _require_owner(request)
    if request.GET.get('__reset'):
        request.session.pop(_BRAIN_DUMP_FILTER_SESSION, None)
        return HttpResponseRedirect(reverse('braindump:dashboard'))

    if filter_query_has_params(request.GET):
        request.session[_BRAIN_DUMP_FILTER_SESSION] = request.GET.urlencode()
        filter_get = request.GET
    else:
        raw = request.session.get(_BRAIN_DUMP_FILTER_SESSION, '')
        filter_get = QueryDict(raw) if raw else QueryDict()

    active_qs = CaptureItem.objects.filter(
        user=request.user, archived=False
    ).order_by('-created_at')
    active_qs = apply_dashboard_filters(active_qs, filter_get)
    active = list(active_qs)
    parts = partition_active_items(active)
    gtd = {
        'unclear': _sort_date_then_priority(parts['unclear']),
        'trash_list': _sort_date_then_priority(parts['trash_list']),
        'reference': _sort_date_then_priority(parts['reference']),
        'someday': _sort_date_then_priority(parts['someday']),
        'calendar_hard': _sort_date_then_priority(parts['calendar_hard']),
        'waiting': _sort_date_then_priority(parts['waiting']),
        'projects': _sort_date_then_priority(parts['projects']),
        'next_actions': _sort_date_then_priority(parts['next_actions']),
    }
    done_qs = CaptureItem.objects.filter(user=request.user, archived=True).order_by(
        '-completed_at'
    )
    done_qs = apply_dashboard_filters(done_qs, filter_get)
    done_limit = 80 if filter_query_has_params(filter_get) else 40
    done_recent = list(done_qs[:done_limit])
    recurring_rules = list(
        RecurringCaptureRule.objects.filter(user=request.user).order_by(
            'next_run_date', 'pk'
        )[:50]
    )
    return render(
        request,
        'braindump/dashboard.html',
        {
            'gtd': gtd,
            'done_recent': done_recent,
            'status_choices': CaptureStatus.choices,
            'task_priority_choices': TaskPriority.choices,
            'gtd_bucket_choices': GTDBucket.choices,
            'engagement_choices': EngagementChoice.choices,
            'max_capture_parts': _MAX_CAPTURE_PARTS,
            'recurring_rules': recurring_rules,
            'recurrence_pattern_choices': RecurrencePattern.choices,
            'weekday_choices': _WEEKDAY_CHOICES,
            'filter_get': filter_get,
            'work_type_choices': work_type_filter_choices(request.user),
            'filters_active': filter_query_has_params(filter_get),
        },
    )


@login_required
@require_http_methods(['POST'])
def recurring_create(request):
    _require_owner(request)
    body = (request.POST.get('recurring_body') or '').strip()
    if not body:
        messages.error(request, 'Add text for the recurring capture.')
        return _dashboard_redirect(request)
    title = (request.POST.get('recurring_title') or '').strip()[:200]
    pattern = (request.POST.get('recurring_pattern') or '').strip()
    valid_p = {c.value for c in RecurrencePattern}
    if pattern not in valid_p:
        messages.error(request, 'Pick a valid recurrence pattern.')
        return _dashboard_redirect(request)
    raw_anchor = (request.POST.get('recurring_anchor') or '').strip()
    try:
        anchor = dt.strptime(raw_anchor, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        anchor = timezone.localdate()

    wd_raw = (request.POST.get('recurring_weekday') or '').strip()
    weekday = None
    if wd_raw != '':
        try:
            w = int(wd_raw)
            if 0 <= w <= 6:
                weekday = w
        except ValueError:
            pass

    try:
        interval = max(1, int(request.POST.get('recurring_interval_weeks') or 2))
    except ValueError:
        interval = 2

    nth_val = None
    raw_nth = (request.POST.get('recurring_nth') or '').strip()
    if raw_nth:
        try:
            nth_val = int(raw_nth)
        except ValueError:
            pass

    dom_val = None
    raw_dom = (request.POST.get('recurring_day_of_month') or '').strip()
    if raw_dom:
        try:
            dom_val = int(raw_dom)
        except ValueError:
            pass

    try:
        next_d = first_run_on_or_after(
            pattern,
            anchor,
            anchor,
            weekday=weekday if weekday is not None else 0,
            interval_weeks=interval,
            nth_of_month=nth_val or 1,
            day_of_month=dom_val or anchor.day,
        )
    except ValueError as e:
        messages.error(request, str(e))
        return _dashboard_redirect(request)

    rule = RecurringCaptureRule(
        user=request.user,
        title=title,
        body=body,
        pattern=pattern,
        weekday=weekday,
        interval_weeks=interval,
        nth_of_month=nth_val,
        day_of_month=dom_val,
        anchor_date=anchor,
        next_run_date=next_d,
    )
    from django.core.exceptions import ValidationError

    try:
        rule.full_clean()
        rule.save()
        messages.success(request, f'Recurring rule saved. Next run: {next_d}.')
    except ValidationError as e:
        messages.error(request, ' '.join(e.messages) or 'Invalid recurring rule.')
    return _dashboard_redirect(request)


@login_required
@require_http_methods(['POST'])
def recurring_toggle(request, pk: int):
    _require_owner(request)
    rule = get_object_or_404(RecurringCaptureRule, pk=pk, user=request.user)
    rule.is_active = not rule.is_active
    rule.save(update_fields=['is_active', 'updated_at'])
    messages.success(
        request,
        'Recurring rule paused.' if not rule.is_active else 'Recurring rule active again.',
    )
    return _dashboard_redirect(request)


@login_required
@require_http_methods(['POST'])
def recurring_delete(request, pk: int):
    _require_owner(request)
    rule = get_object_or_404(RecurringCaptureRule, pk=pk, user=request.user)
    rule.delete()
    messages.success(request, 'Recurring rule removed.')
    return _dashboard_redirect(request)


@login_required
@require_http_methods(['POST'])
def morning_digest_send_now(request):
    _require_owner(request)
    result = run_morning_digest_send()
    if result['ok']:
        messages.success(request, result['message'])
    else:
        messages.error(request, result['message'])
    return _dashboard_redirect(request)


@login_required
@require_http_methods(['POST'])
def capture_create(request):
    _require_owner(request)
    body = (request.POST.get('body') or '').strip()
    segments = _split_capture_body(body)
    if not segments:
        return _dashboard_redirect(request)
    for chunk in segments:
        item = CaptureItem.objects.create(user=request.user, body=chunk)
        categorize_capture_item(item)
    return _dashboard_redirect(request)


@login_required
@require_http_methods(['POST'])
def item_status(request, pk: int):
    _require_owner(request)
    item = get_object_or_404(CaptureItem, pk=pk, user=request.user)
    st = (request.POST.get('status') or '').strip()
    removed = False
    if st == CaptureStatus.DONE:
        item.mark_done()
        removed = True
    elif st == CaptureStatus.WAITING:
        item.mark_waiting(request.POST.get('waiting_for', ''))
    elif st == CaptureStatus.OPEN:
        item.mark_open()
    jr = _json_capture_response(request, item, removed=removed)
    if jr:
        return jr
    return _dashboard_redirect(request)


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
    return _dashboard_redirect(request)


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
    update_fields = ['category_label', 'priority', 'updated_at']
    if 'title' in request.POST:
        item.title = (request.POST.get('title') or '').strip()[:200]
        update_fields.append('title')
    if 'body' in request.POST:
        item.body = (request.POST.get('body') or '').strip()
        update_fields.append('body')
    item.save(update_fields=update_fields)
    jr = _json_capture_response(request, item, removed=False)
    if jr:
        return jr
    return _dashboard_redirect(request)


@login_required
@require_http_methods(['POST'])
def item_archive(request, pk: int):
    _require_owner(request)
    item = get_object_or_404(CaptureItem, pk=pk, user=request.user)
    item.archived = True
    item.save(update_fields=['archived', 'updated_at'])
    if _accepts_json(request):
        return JsonResponse({'ok': True, 'removed': True, 'pk': item.pk})
    return _dashboard_redirect(request)


@login_required
@require_http_methods(['POST'])
def recategorize(request, pk: int):
    _require_owner(request)
    item = get_object_or_404(CaptureItem, pk=pk, user=request.user)
    categorize_capture_item(item)
    jr = _json_capture_response(request, item, removed=False)
    if jr:
        return jr
    return _dashboard_redirect(request)
