from django import template
from django.utils import timezone

register = template.Library()


def format_timesince_short(value):
    """Short relative time string for a timezone-aware datetime."""
    if value is None:
        return ''
    now = timezone.now()
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    delta = now - value
    if delta.total_seconds() < 0:
        delta = -delta
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return 'just now'
    minutes = seconds // 60
    if minutes < 60:
        return f'{minutes}m ago'
    hours = seconds // 3600
    if hours < 24:
        return f'{hours}h ago'
    days = delta.days
    if days < 7:
        return f'{days}d ago'
    return f'{value.strftime("%b")} {value.day}'


@register.filter(name='timesince_short')
def timesince_short(value):
    return format_timesince_short(value)
