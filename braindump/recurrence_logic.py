"""Compute next run dates for recurring braindump captures (stdlib only)."""

from __future__ import annotations

import calendar
from datetime import date, timedelta

# Python weekday: Monday=0 .. Sunday=6


def last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    last_d = calendar.monthrange(year, month)[1]
    d = date(year, month, last_d)
    while d.weekday() != weekday:
        d -= timedelta(days=1)
    return d


def nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    if n < 1 or n > 4:
        raise ValueError('n must be 1-4')
    d = date(year, month, 1)
    seen = 0
    while d.month == month:
        if d.weekday() == weekday:
            seen += 1
            if seen == n:
                return d
        d += timedelta(days=1)
    raise ValueError(f'No {n}th weekday in {year}-{month:02d}')


def next_calendar_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def next_weekday_on_or_after(d: date, weekday: int) -> date:
    delta = (weekday - d.weekday()) % 7
    return d + timedelta(days=delta)


def first_every_n_weeks_on_or_after(
    anchor: date, interval_weeks: int, on_or_after: date
) -> date:
    if interval_weeks < 1:
        interval_weeks = 1
    step = timedelta(weeks=interval_weeks)
    d = anchor
    guard = 0
    while d < on_or_after and guard < 5000:
        d += step
        guard += 1
    return d


def first_monthly_last_on_or_after(start: date, weekday: int) -> date:
    d = last_weekday_of_month(start.year, start.month, weekday)
    if d >= start:
        return d
    y, m = next_calendar_month(start.year, start.month)
    return last_weekday_of_month(y, m, weekday)


def first_monthly_nth_on_or_after(start: date, weekday: int, n: int) -> date:
    try:
        d = nth_weekday_of_month(start.year, start.month, weekday, n)
    except ValueError:
        d = None
    if d is not None and d >= start:
        return d
    y, m = next_calendar_month(start.year, start.month)
    return nth_weekday_of_month(y, m, weekday, n)


def first_monthly_day_on_or_after(start: date, day: int) -> date:
    last = calendar.monthrange(start.year, start.month)[1]
    dom = min(max(1, day), last)
    d = date(start.year, start.month, dom)
    if d >= start:
        return d
    y, m = next_calendar_month(start.year, start.month)
    last2 = calendar.monthrange(y, m)[1]
    dom2 = min(max(1, day), last2)
    return date(y, m, dom2)


def advance_after_spawn(pattern: str, current_run: date, **kwargs) -> date:
    """Next occurrence strictly after ``current_run`` (the day we just spawned)."""
    weekday = kwargs.get('weekday')
    if weekday is None:
        weekday = 0

    if pattern == 'weekly':
        return current_run + timedelta(weeks=1)

    if pattern == 'every_n_weeks':
        n = int(kwargs.get('interval_weeks') or 2)
        return current_run + timedelta(weeks=n)

    if pattern == 'monthly_last':
        y, m = next_calendar_month(current_run.year, current_run.month)
        return last_weekday_of_month(y, m, weekday)

    if pattern == 'monthly_nth':
        nth = int(kwargs.get('nth_of_month') or 1)
        y, m = next_calendar_month(current_run.year, current_run.month)
        return nth_weekday_of_month(y, m, weekday, nth)

    if pattern == 'monthly_day':
        dom = int(kwargs.get('day_of_month') or 1)
        y, m = next_calendar_month(current_run.year, current_run.month)
        last = calendar.monthrange(y, m)[1]
        return date(y, m, min(max(1, dom), last))

    return current_run + timedelta(weeks=1)


def first_run_on_or_after(
    pattern: str, anchor: date, on_or_after: date, **kwargs
) -> date:
    weekday = kwargs.get('weekday')
    if weekday is None:
        weekday = 0

    if pattern == 'weekly':
        d = next_weekday_on_or_after(anchor, weekday)
        while d < on_or_after:
            d += timedelta(weeks=1)
        return d

    if pattern == 'every_n_weeks':
        n = int(kwargs.get('interval_weeks') or 2)
        return first_every_n_weeks_on_or_after(anchor, n, on_or_after)

    if pattern == 'monthly_last':
        return first_monthly_last_on_or_after(on_or_after, weekday)

    if pattern == 'monthly_nth':
        nth = int(kwargs.get('nth_of_month') or 1)
        return first_monthly_nth_on_or_after(on_or_after, weekday, nth)

    if pattern == 'monthly_day':
        dom = int(kwargs.get('day_of_month') or anchor.day)
        return first_monthly_day_on_or_after(on_or_after, dom)

    return on_or_after
