"""Build month grid + items not on the hard-date grid for the monthly email."""

from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date

from django.db.models import QuerySet
from django.utils import timezone

from .contact_calendar import merge_contact_birthdays_into_by_day
from .models import CaptureItem, TaskPriority
from .office_mdh_schedule import merge_mdh_holds_into_by_day

_PRIO_RANK = {
    TaskPriority.URGENT: 0,
    TaskPriority.HIGH: 1,
    TaskPriority.NORMAL: 2,
    TaskPriority.LOW: 3,
}


def _cal_sort_key(x):
    if getattr(x, 'synthetic_office_hold', False):
        return (0, 0, 0.0)
    if getattr(x, 'synthetic_contact_birthday', False):
        created = getattr(x, 'created_at', None)
        return (1, 0, -(created.timestamp() if created else 0.0))
    pr = _PRIO_RANK.get(getattr(x, 'priority', TaskPriority.NORMAL), 2)
    created = getattr(x, 'created_at', None)
    return (2, pr, -(created.timestamp() if created else 0.0))


def build_month_calendar_context(
    *,
    year: int,
    month: int,
    qs: QuerySet[CaptureItem],
    calendar_user=None,
) -> dict:
    """``qs`` should already be filtered to the owning user and target month scope."""
    by_day: dict[date, list[CaptureItem]] = defaultdict(list)
    unscheduled: list[CaptureItem] = []
    soft_dated: list[CaptureItem] = []

    for item in qs:
        if item.calendar_date and item.calendar_date.year == year and item.calendar_date.month == month:
            if item.calendar_is_hard_date:
                by_day[item.calendar_date].append(item)
            else:
                soft_dated.append(item)
            continue
        created = timezone.localtime(item.created_at).date()
        if created.year == year and created.month == month:
            unscheduled.append(item)

    merge_mdh_holds_into_by_day(by_day, year, month)
    if calendar_user is not None:
        merge_contact_birthdays_into_by_day(by_day, year, month, calendar_user)
    for _d, lst in by_day.items():
        lst.sort(key=_cal_sort_key)

    cal = calendar.Calendar(firstweekday=6)
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        row = []
        for d in week:
            if d.month != month:
                row.append({'in_month': False, 'day': None, 'date': None, 'items': []})
            else:
                row.append(
                    {
                        'in_month': True,
                        'day': d.day,
                        'date': d,
                        'items': by_day.get(d, []),
                    }
                )
        weeks.append(row)

    return {
        'year': year,
        'month': month,
        'weeks': weeks,
        'unscheduled': unscheduled,
        'soft_dated': soft_dated,
    }
