from django import template
from django.urls import reverse

from nomoar.utils import map_filter_querystring, timeline_filter_querystring

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


@register.simple_tag(takes_context=True)
def map_url(context, **overrides):
    """Build map URL preserving current map filters; override e.g. focus=slug."""
    request = context['request']
    qs = map_filter_querystring(request, **overrides)
    base = reverse('nomoar:map')
    return f'{base}?{qs}' if qs else base


@register.simple_tag(takes_context=True)
def timeline_url_from_map(context, **extra):
    """Timeline URL carrying current map filters (type, state, q, decade from years)."""
    from urllib.parse import urlencode

    request = context['request']
    from nomoar.utils import timeline_params_from_map_get

    base = reverse('nomoar:timeline')
    params = timeline_params_from_map_get(request.GET)
    for k, v in extra.items():
        if v not in (None, ''):
            params[k] = v
    qs = urlencode(sorted((k, v) for k, v in params.items() if v))
    return f'{base}?{qs}' if qs else base
