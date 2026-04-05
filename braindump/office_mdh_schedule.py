"""
Alternating MDH "in office" blocks (not tasks): Tue–Wed–Thu one week, Tue–Wed the next,
8:00–17:00 local time, skipping US federal holidays. Merged into calendar views and AI context.
"""

from __future__ import annotations

import calendar as cal_mod
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.utils import timezone

from .models import (
    CaptureStatus,
    EngagementChoice,
    GTDBucket,
    NonActionableDisposition,
    TaskPriority,
)

# Monday=0 … Sunday=6
_TUE, _WED, _THU = 1, 2, 3


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _observed_weekday_off(d: date) -> date:
    """US federal-style: Sat holiday -> Fri; Sun holiday -> Mon."""
    wd = d.weekday()
    if wd == 5:
        return d - timedelta(days=1)
    if wd == 6:
        return d + timedelta(days=1)
    return d


def _nth_weekday_in_month(year: int, month: int, weekday: int, n: int) -> date | None:
    """n=1 first weekday of month, etc."""
    _, last = cal_mod.monthrange(year, month)
    count = 0
    for day in range(1, last + 1):
        d = date(year, month, day)
        if d.weekday() == weekday:
            count += 1
            if count == n:
                return d
    return None


def _last_weekday_in_month(year: int, month: int, weekday: int) -> date | None:
    _, last = cal_mod.monthrange(year, month)
    for day in range(last, 0, -1):
        d = date(year, month, day)
        if d.weekday() == weekday:
            return d
    return None


def _fourth_thursday_november(year: int) -> date | None:
    return _nth_weekday_in_month(year, 11, 3, 4)


def us_federal_holiday_observed_dates(year: int) -> set[date]:
    """Observed US federal public holidays that fall in ``year`` OR are observed on a date in ``year``."""
    out: set[date] = set()
    for d in (
        _nth_weekday_in_month(year, 1, 0, 3),
        _nth_weekday_in_month(year, 2, 0, 3),
        _last_weekday_in_month(year, 5, 0),
        _nth_weekday_in_month(year, 9, 0, 1),
        _nth_weekday_in_month(year, 10, 0, 2),
        _fourth_thursday_november(year),
    ):
        if d:
            out.add(d)
    for m, da in ((6, 19), (11, 11)):
        out.add(_observed_weekday_off(date(year, m, da)))
    out.add(_observed_weekday_off(date(year, 7, 4)))
    out.add(_observed_weekday_off(date(year, 12, 25)))
    out.add(_observed_weekday_off(date(year, 1, 1)))
    return out


def is_us_federal_holiday(d: date) -> bool:
    """True if ``d`` is an observed US federal public holiday (weekday off)."""
    for y in (d.year - 1, d.year, d.year + 1):
        if d in us_federal_holiday_observed_dates(y):
            return True
    return False


def mdh_office_long_week_anchor() -> date:
    """
    A Monday whose week is a "long" MDH office week (Tue–Wed–Thu in office).
    Override with settings.BRAINDUMP_MDH_OFFICE_LONG_WEEK_ANCHOR (ISO date string, must be Monday).
    """
    raw = (getattr(settings, 'BRAINDUMP_MDH_OFFICE_LONG_WEEK_ANCHOR', '') or '').strip()
    if raw:
        try:
            anchor = date.fromisoformat(raw[:10])
            return _monday_of(anchor)
        except ValueError:
            pass
    return date(2026, 1, 5)


def is_long_mdh_office_week(week_monday: date) -> bool:
    anchor = mdh_office_long_week_anchor()
    delta_weeks = (week_monday - anchor).days // 7
    return delta_weeks % 2 == 0


def mdh_office_weekdays_for(week_monday: date) -> tuple[int, ...]:
    """Weekday indices (Mon=0) that are MDH in-office days for this ISO week."""
    if is_long_mdh_office_week(week_monday):
        return (_TUE, _WED, _THU)
    return (_TUE, _WED)


def is_mdh_office_day(d: date) -> bool:
    if not getattr(settings, 'BRAINDUMP_MDH_OFFICE_ENABLED', True):
        return False
    mon = _monday_of(d)
    if d.weekday() not in mdh_office_weekdays_for(mon):
        return False
    if is_us_federal_holiday(d):
        return False
    return True


def mdh_office_time_window_label() -> str:
    start = getattr(settings, 'BRAINDUMP_MDH_OFFICE_START', '08:00')
    end = getattr(settings, 'BRAINDUMP_MDH_OFFICE_END', '17:00')
    return f'{start}–{end} local time'


@dataclass
class OfficeHoldCalendarEntry:
    """Display-only calendar row: not a DB CaptureItem, not an actionable task."""

    synthetic_office_hold: bool = field(default=True, init=False)
    pk: int | None = field(default=None, init=False)
    title: str = ''
    body: str = ''
    category_label: str = 'MDH'
    priority: str = TaskPriority.LOW
    status: str = CaptureStatus.OPEN
    gtd_bucket: str = GTDBucket.CALENDAR
    is_actionable: bool = False
    non_actionable_disposition: str = NonActionableDisposition.REFERENCE
    is_project: bool = False
    calendar_date: date | None = None
    calendar_is_hard_date: bool = True
    waiting_for: str = ''
    next_action: str = ''
    engagement: str = ''
    two_minute_rule_suggested: bool = False
    archived: bool = False
    ai_error: str = ''
    ai_payload: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=timezone.now)

    def get_priority_display(self) -> str:
        return TaskPriority(self.priority).label

    def get_status_display(self) -> str:
        return CaptureStatus(self.status).label

    def get_gtd_bucket_display(self) -> str:
        return GTDBucket(self.gtd_bucket).label

    def get_non_actionable_disposition_display(self) -> str:
        if not self.non_actionable_disposition:
            return '—'
        return NonActionableDisposition(self.non_actionable_disposition).label

    def get_engagement_display(self) -> str:
        if not self.engagement:
            return ''
        try:
            return EngagementChoice(self.engagement).label
        except ValueError:
            return self.engagement


def make_office_hold_entry(d: date) -> OfficeHoldCalendarEntry:
    mon = _monday_of(d)
    long_w = is_long_mdh_office_week(mon)
    week_kind = 'Tue–Wed–Thu' if long_w else 'Tue–Wed'
    win = mdh_office_time_window_label()
    title = f'Work in office (MDH) {win}'
    body = (
        f'Standing availability block (not a task): MDH office {week_kind} this week, '
        f'{win}. You are not available for other commitments during these hours unless noted.'
    )
    return OfficeHoldCalendarEntry(
        title=title,
        body=body,
        calendar_date=d,
        created_at=timezone.make_aware(datetime.combine(d, time.min)),
    )


def iter_mdh_office_days(d0: date, d1: date):
    d = d0
    while d <= d1:
        if is_mdh_office_day(d):
            yield d
        d += timedelta(days=1)


def office_holds_between(d0: date, d1: date) -> list[OfficeHoldCalendarEntry]:
    return [make_office_hold_entry(d) for d in iter_mdh_office_days(d0, d1)]


def format_mdh_availability_for_ai(d0: date, d1: date) -> str:
    """Human-readable block for the LLM user message."""
    if not getattr(settings, 'BRAINDUMP_MDH_OFFICE_ENABLED', True):
        return ''
    lines = [
        'Owner recurring MDH office blocks (NOT actionable tasks; owner is unavailable for '
        'other daytime commitments during these windows):',
        f'  • Alternating weeks: one week Tue+Wed+Thu; the next week Tue+Wed only (local time), '
        f'{mdh_office_time_window_label()}.',
        '  • US federal holidays are excluded (no office block on that date).',
        '  • If a capture implies a meeting, appointment, travel, or other daytime obligation '
        'outside MDH during these blocks on the same calendar day, set scheduling_note in JSON.',
    ]
    days = list(iter_mdh_office_days(d0, d1))
    if not days:
        lines.append(f'  (No MDH office days in range {d0}..{d1}.)')
    else:
        lines.append(f'  MDH office days {d0} .. {d1}:')
        for d in days[:42]:
            mon = _monday_of(d)
            tag = 'long' if is_long_mdh_office_week(mon) else 'short'
            lines.append(f'    - {d.isoformat()} ({d.strftime("%A")}, {tag} week)')
        if len(days) > 42:
            lines.append(f'    … and {len(days) - 42} more day(s).')
    return '\n'.join(lines)


def merge_mdh_holds_into_by_day(
    by_day: dict[date, list],
    year: int,
    month: int,
) -> None:
    """Mutate ``by_day`` in place: add synthetic office holds for days in that month."""
    if not getattr(settings, 'BRAINDUMP_MDH_OFFICE_ENABLED', True):
        return
    _, last = cal_mod.monthrange(year, month)
    for day in range(1, last + 1):
        d = date(year, month, day)
        if not is_mdh_office_day(d):
            continue
        hold = make_office_hold_entry(d)
        by_day.setdefault(d, []).append(hold)


def merge_office_holds_with_capture_calendar(
    captures: list,
    d0: date,
    d1: date,
) -> list:
    """Sorted list of CaptureItem + OfficeHoldCalendarEntry for dashboard digest-style lists."""
    holds = office_holds_between(d0, d1)
    by_date: dict[date, list] = {}
    for it in captures:
        if getattr(it, 'calendar_date', None):
            by_date.setdefault(it.calendar_date, []).append(it)
    for h in holds:
        by_date.setdefault(h.calendar_date, []).append(h)
    out: list = []
    for d in sorted(by_date.keys()):
        row = by_date[d]
        _pri = {
            TaskPriority.URGENT: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.LOW: 3,
        }
        row.sort(
            key=lambda x: (
                0 if getattr(x, 'synthetic_office_hold', False) else 1,
                _pri.get(getattr(x, 'priority', TaskPriority.NORMAL), 2),
            )
        )
        out.extend(row)
    return out


def calendar_date_range_for_merges(
    captures: list, today: date, *, pad_days: int = 120
) -> tuple[date, date]:
    dates = [it.calendar_date for it in captures if getattr(it, 'calendar_date', None)]
    d0 = min(dates) if dates else today
    d1 = max(dates) if dates else today
    d0 = min(d0, today)
    d1 = max(d1, today + timedelta(days=pad_days))
    return d0, d1
