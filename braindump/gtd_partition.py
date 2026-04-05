"""Split active CaptureItems into GTD organize lists (Allen: calendar vs next actions vs etc.)."""

from __future__ import annotations

from .models import (
    CaptureItem,
    CaptureStatus,
    GTDBucket,
    NonActionableDisposition,
)


def partition_active_items(items: list[CaptureItem]) -> dict[str, list[CaptureItem]]:
    """
    Each item appears in at most one primary list (first match wins).
    Order: unclear inbox → trash (non-actionable) → reference → someday →
    calendar (hard date) → waiting → projects → next actions.
    """
    unclear: list[CaptureItem] = []
    trash_list: list[CaptureItem] = []
    reference: list[CaptureItem] = []
    someday: list[CaptureItem] = []
    calendar_hard: list[CaptureItem] = []
    waiting: list[CaptureItem] = []
    projects: list[CaptureItem] = []
    next_actions: list[CaptureItem] = []

    for it in items:
        if it.is_actionable is None:
            unclear.append(it)
            continue
        if it.is_actionable is False:
            if it.non_actionable_disposition == NonActionableDisposition.TRASH:
                trash_list.append(it)
            elif it.non_actionable_disposition == NonActionableDisposition.REFERENCE:
                reference.append(it)
            elif it.non_actionable_disposition == NonActionableDisposition.SOMEDAY:
                someday.append(it)
            else:
                someday.append(it)
            continue
        if it.calendar_is_hard_date and it.calendar_date:
            calendar_hard.append(it)
            continue
        if it.status == CaptureStatus.WAITING or it.gtd_bucket == GTDBucket.WAITING:
            waiting.append(it)
            continue
        if it.is_project or it.gtd_bucket == GTDBucket.PROJECT:
            projects.append(it)
            continue
        if it.gtd_bucket in (GTDBucket.SOMEDAY,):
            someday.append(it)
            continue
        if it.gtd_bucket == GTDBucket.REFERENCE:
            reference.append(it)
            continue
        next_actions.append(it)

    return {
        'unclear': unclear,
        'trash_list': trash_list,
        'reference': reference,
        'someday': someday,
        'calendar_hard': calendar_hard,
        'waiting': waiting,
        'projects': projects,
        'next_actions': next_actions,
    }
