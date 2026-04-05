"""Contact birthdays as synthetic calendar entries (month grid + digest)."""

from __future__ import annotations

import calendar as cal_mod
from dataclasses import dataclass, field
from datetime import date, datetime, time

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    CaptureStatus,
    EngagementChoice,
    GTDBucket,
    NonActionableDisposition,
    PersonalContact,
    TaskPriority,
)

User = get_user_model()


def birthday_on_calendar_date(birth_date: date, year: int, month: int) -> date | None:
    """Return the calendar date in ``year``/``month`` for this birthday, or None."""
    if birth_date.month != month:
        return None
    try:
        return date(year, birth_date.month, birth_date.day)
    except ValueError:
        if birth_date.month == 2 and birth_date.day == 29 and not cal_mod.isleap(year):
            return date(year, 2, 28)
        return None


def birthday_falls_on_date(birth_date: date, d: date) -> bool:
    """True if the annual birthday for ``birth_date`` is observed on calendar day ``d``."""
    if birth_date.month == 2 and birth_date.day == 29:
        if cal_mod.isleap(d.year):
            return d.month == 2 and d.day == 29
        return d.month == 2 and d.day == 28
    return (birth_date.month, birth_date.day) == (d.month, d.day)


@dataclass
class ContactBirthdayCalendarEntry:
    """Display-only birthday reminder on the calendar (not a capture)."""

    synthetic_contact_birthday: bool = field(default=True, init=False)
    pk: int | None = field(default=None, init=False)
    title: str = ''
    body: str = ''
    category_label: str = ''
    priority: str = TaskPriority.NORMAL
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


def make_birthday_entry(contact: PersonalContact, on_date: date) -> ContactBirthdayCalendarEntry:
    age = on_date.year - contact.birth_date.year
    title = f"🎂 {contact.display_name}'s birthday"
    body = f'{contact.display_name} turns {age} (born {contact.birth_date.strftime("%b %d, %Y")}).'
    return ContactBirthdayCalendarEntry(
        title=title,
        body=body,
        calendar_date=on_date,
        created_at=timezone.make_aware(datetime.combine(on_date, time.min)),
    )


def merge_contact_birthdays_into_by_day(
    by_day: dict[date, list],
    year: int,
    month: int,
    user: User,
) -> None:
    """Append birthday chips for contacts with birth_date in this month."""
    qs = PersonalContact.objects.filter(user=user, birth_date__isnull=False).only(
        'display_name', 'birth_date'
    )
    for c in qs:
        d = birthday_on_calendar_date(c.birth_date, year, month)
        if not d:
            continue
        by_day.setdefault(d, []).append(make_birthday_entry(c, d))


def birthday_entries_for_date(user: User, d: date) -> list[ContactBirthdayCalendarEntry]:
    """All contact birthdays on a specific calendar day."""
    out: list[ContactBirthdayCalendarEntry] = []
    qs = PersonalContact.objects.filter(user=user, birth_date__isnull=False).only(
        'display_name', 'birth_date'
    )
    for c in qs:
        if birthday_falls_on_date(c.birth_date, d):
            out.append(make_birthday_entry(c, d))
    return out
