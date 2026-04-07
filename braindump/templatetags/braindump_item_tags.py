"""Template helpers for capture item cards (sort keys, etc.)."""

from django import template

from braindump.models import TaskPriority

register = template.Library()

_PRI = {
    TaskPriority.URGENT: 0,
    TaskPriority.HIGH: 1,
    TaskPriority.NORMAL: 2,
    TaskPriority.LOW: 3,
}


@register.filter
def priority_rank(value: str) -> int:
    return _PRI.get(value, 2)
