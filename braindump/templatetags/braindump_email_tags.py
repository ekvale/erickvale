"""Email-safe colors for work stream + priority (morning digest, calendar)."""

from __future__ import annotations

from django import template

from braindump.models import TaskPriority
from braindump.work_category import CATEGORY_DREAM_BLUE, CATEGORY_MDH, CATEGORY_SIOUX_CHEF

register = template.Library()

_STREAM = {
    CATEGORY_MDH: {
        'card_bg': '#eff6ff',
        'card_border': '#bfdbfe',
        'chip_bg': '#dbeafe',
        'badge_bg': '#1d4ed8',
        'badge_fg': '#ffffff',
    },
    CATEGORY_DREAM_BLUE: {
        'card_bg': '#ecfeff',
        'card_border': '#a5f3fc',
        'chip_bg': '#cffafe',
        'badge_bg': '#0e7490',
        'badge_fg': '#ffffff',
    },
    CATEGORY_SIOUX_CHEF: {
        'card_bg': '#fffbeb',
        'card_border': '#fde68a',
        'chip_bg': '#fef3c7',
        'badge_bg': '#c2410c',
        'badge_fg': '#ffffff',
    },
}
_DEFAULT_STREAM = {
    'card_bg': '#f6f8fa',
    'card_border': '#d0d7de',
    'chip_bg': '#eaeef2',
    'badge_bg': '#57606a',
    'badge_fg': '#ffffff',
}

_PRIORITY = {
    TaskPriority.URGENT: {
        'accent': '#dc2626',
        'label_bg': '#fee2e2',
        'label_fg': '#991b1b',
    },
    TaskPriority.HIGH: {
        'accent': '#ea580c',
        'label_bg': '#ffedd5',
        'label_fg': '#9a3412',
    },
    TaskPriority.NORMAL: {
        'accent': '#2563eb',
        'label_bg': '#dbeafe',
        'label_fg': '#1e40af',
    },
    TaskPriority.LOW: {
        'accent': '#6b7280',
        'label_bg': '#f3f4f6',
        'label_fg': '#374151',
    },
}


def _stream_for_label(label: str | None) -> dict:
    key = (label or '').strip()
    return _STREAM.get(key, _DEFAULT_STREAM)


def _priority_for_value(priority: str | None) -> dict:
    if not priority:
        return _PRIORITY[TaskPriority.NORMAL]
    return _PRIORITY.get(priority, _PRIORITY[TaskPriority.NORMAL])


@register.inclusion_tag('braindump/emails/_digest_item_card.html')
def digest_item_card(it, show_next=True, show_priority=True, show_meta=True):
    """Card row for digest lists (next actions, waiting, projects, etc.)."""
    stream = _stream_for_label(getattr(it, 'category_label', None))
    pri = _priority_for_value(getattr(it, 'priority', None))
    return {
        'it': it,
        'stream': stream,
        'pri': pri,
        'show_next': show_next,
        'show_priority': show_priority,
        'show_meta': show_meta,
    }


@register.inclusion_tag('braindump/emails/_digest_calendar_chip.html')
def digest_calendar_chip(it):
    """Small chip inside month grid cells."""
    stream = _stream_for_label(getattr(it, 'category_label', None))
    pri = _priority_for_value(getattr(it, 'priority', None))
    is_hold = bool(getattr(it, 'synthetic_office_hold', False))
    return {
        'it': it,
        'stream': stream,
        'pri': pri,
        'is_mdh_office_hold': is_hold,
    }
