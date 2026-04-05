"""Materialize recurring capture rules into CaptureItem rows."""

from __future__ import annotations

import logging
from datetime import date

from django.db import transaction
from django.utils import timezone

from .ai_categorize import categorize_capture_item
from .models import CaptureItem, RecurringCaptureRule
from .recurrence_logic import advance_after_spawn

logger = logging.getLogger(__name__)

# Avoid dozens of LLM calls if next_run was neglected for months.
_MAX_CATCH_UP = 24


def _spawn_single_rule(rule: RecurringCaptureRule) -> None:
    run_day = rule.next_run_date
    wd = rule.weekday if rule.weekday is not None else 0
    item = CaptureItem.objects.create(
        user=rule.user,
        body=rule.body,
        title=(rule.title or rule.body)[:200],
        calendar_date=run_day,
        calendar_is_hard_date=False,
        spawned_from_recurring=rule,
    )
    categorize_capture_item(item)
    item.refresh_from_db()
    item.calendar_date = run_day
    item.calendar_is_hard_date = False
    item.save(update_fields=['calendar_date', 'calendar_is_hard_date', 'updated_at'])

    nxt = advance_after_spawn(
        rule.pattern,
        run_day,
        weekday=wd,
        interval_weeks=rule.interval_weeks,
        nth_of_month=rule.nth_of_month or 1,
        day_of_month=rule.day_of_month or 1,
    )
    rule.next_run_date = nxt
    rule.last_spawned_at = timezone.now()
    rule.save(update_fields=['next_run_date', 'last_spawned_at', 'updated_at'])


def process_recurring_captures_for_owner(owner, as_of: date) -> int:
    """
    For active rules with next_run_date <= as_of, create capture(s) and advance.
    Catches up missed runs (up to MAX_CATCH_UP per rule per invocation).
    """
    ids = list(
        RecurringCaptureRule.objects.filter(
            user=owner,
            is_active=True,
            next_run_date__lte=as_of,
        ).values_list('pk', flat=True)
    )
    total = 0
    for rid in ids:
        try:
            with transaction.atomic():
                rule = (
                    RecurringCaptureRule.objects.select_for_update()
                    .filter(pk=rid, is_active=True)
                    .first()
                )
                if rule is None or rule.next_run_date > as_of:
                    continue
                n = 0
                while rule.next_run_date <= as_of and n < _MAX_CATCH_UP:
                    _spawn_single_rule(rule)
                    n += 1
                    total += 1
                    rule.refresh_from_db()
        except Exception as e:
            logger.exception('braindump recurring spawn failed for rule %s: %s', rid, e)
    return total
