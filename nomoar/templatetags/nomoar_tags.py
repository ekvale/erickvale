from django import template
from django.urls import reverse

from nomoar.utils import timeline_filter_querystring

register = template.Library()


@register.simple_tag(takes_context=True)
def timeline_url(context, **overrides):
    """Build timeline URL with current filters, overridden by keyword args (use None to drop)."""
    request = context['request']
    qs = timeline_filter_querystring(request, **overrides)
    base = reverse('nomoar:timeline')
    return f'{base}?{qs}' if qs else base


@register.simple_tag(takes_context=True)
def timeline_full_url(context):
    """Absolute URL for copy-link (includes query string)."""
    request = context['request']
    return request.build_absolute_uri()
