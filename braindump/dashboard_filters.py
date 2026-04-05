"""GET-query filters for the braindump dashboard lists."""

from __future__ import annotations

import operator
from datetime import date, datetime
from functools import reduce
from typing import Any

from django.db.models import Q, QuerySet

from .models import (
    CaptureItem,
    CaptureStatus,
    EngagementChoice,
    GTDBucket,
    TaskPriority,
)
from .work_category import CATEGORY_DREAM_BLUE, CATEGORY_MDH, CATEGORY_SIOUX_CHEF

KNOWN_WORK_TYPES = (CATEGORY_MDH, CATEGORY_DREAM_BLUE, CATEGORY_SIOUX_CHEF)

_FILTER_KEYS = frozenset(
    {
        'person',
        'q',
        'work_type',
        'gtd_bucket',
        'priority',
        'status',
        'engagement',
        'is_actionable',
        'is_project',
        'recurring_spawn',
        'due_from',
        'due_to',
        'include_undated',
        'created_from',
        'created_to',
    }
)


def _parse_date(val: Any) -> date | None:
    if val is None:
        return None
    s = str(val).strip()[:10]
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None


def apply_dashboard_filters(
    qs: QuerySet[CaptureItem], params: dict[str, Any]
) -> QuerySet[CaptureItem]:
    """Narrow a CaptureItem queryset using dashboard GET parameters."""
    person = (params.get('person') or params.get('q') or '').strip()
    if person:
        qs = qs.filter(
            Q(title__icontains=person)
            | Q(body__icontains=person)
            | Q(waiting_for__icontains=person)
            | Q(next_action__icontains=person)
        )

    work = (params.get('work_type') or '').strip()
    if work == '__other__':
        qs = qs.exclude(category_label__in=list(KNOWN_WORK_TYPES)).exclude(
            category_label=''
        )
    elif work:
        qs = qs.filter(category_label=work)

    bucket = (params.get('gtd_bucket') or '').strip()
    if bucket in {c.value for c in GTDBucket}:
        qs = qs.filter(gtd_bucket=bucket)

    pri = (params.get('priority') or '').strip()
    if pri in {c.value for c in TaskPriority}:
        qs = qs.filter(priority=pri)

    st = (params.get('status') or '').strip()
    if st in {c.value for c in CaptureStatus}:
        qs = qs.filter(status=st)

    eng = (params.get('engagement') or '').strip()
    if eng in {c.value for c in EngagementChoice}:
        qs = qs.filter(engagement=eng)

    ia = (params.get('is_actionable') or '').strip()
    if ia == 'yes':
        qs = qs.filter(is_actionable=True)
    elif ia == 'no':
        qs = qs.filter(is_actionable=False)
    elif ia == 'unclear':
        qs = qs.filter(is_actionable__isnull=True)

    ip = (params.get('is_project') or '').strip()
    if ip == '1':
        qs = qs.filter(is_project=True)
    elif ip == '0':
        qs = qs.filter(is_project=False)

    if (params.get('recurring_spawn') or '').strip() in ('1', 'on', 'true', 'yes'):
        qs = qs.filter(spawned_from_recurring__isnull=False)

    df = _parse_date(params.get('due_from'))
    dt = _parse_date(params.get('due_to'))
    if df or dt:
        inc_undated = (params.get('include_undated') or '').strip().lower() in (
            '1',
            'on',
            'true',
            'yes',
        )
        pieces: list[Q] = []
        if inc_undated:
            pieces.append(Q(calendar_date__isnull=True))
        cal = Q(calendar_date__isnull=False)
        if df:
            cal &= Q(calendar_date__gte=df)
        if dt:
            cal &= Q(calendar_date__lte=dt)
        pieces.append(cal)
        qs = qs.filter(reduce(operator.or_, pieces))

    cf = _parse_date(params.get('created_from'))
    ct = _parse_date(params.get('created_to'))
    if cf:
        qs = qs.filter(created_at__date__gte=cf)
    if ct:
        qs = qs.filter(created_at__date__lte=ct)

    return qs


def work_type_filter_choices(user) -> list[tuple[str, str]]:
    """Known streams plus distinct labels from this user's items."""
    out: list[tuple[str, str]] = [
        ('', 'All work types'),
        (CATEGORY_MDH, 'MDH'),
        (CATEGORY_DREAM_BLUE, 'Dream Blue'),
        (CATEGORY_SIOUX_CHEF, 'Sioux Chef'),
        ('__other__', 'Other (custom label)'),
    ]
    seen = {t[0] for t in out}
    extra = (
        CaptureItem.objects.filter(user=user)
        .exclude(category_label='')
        .values_list('category_label', flat=True)
        .distinct()
        .order_by('category_label')[:40]
    )
    for lab in extra:
        if lab and lab not in seen:
            out.append((lab, lab))
            seen.add(lab)
    return out


def filter_query_has_params(get_dict) -> bool:
    return any(k in _FILTER_KEYS for k in get_dict.keys())
