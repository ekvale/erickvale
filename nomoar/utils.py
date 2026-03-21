"""Shared helpers for NOMOAR views and templates."""
from urllib.parse import urlencode


def timeline_filter_querystring(request, **overrides):
    """
    Build query string for timeline filters. Keys: decade, q, type, state, page.
    Pass key='' or None to remove from output (e.g. decade='' for All Time).
    Page is only added when passed explicitly in overrides (not copied from request).
    """
    skip = {k for k, v in overrides.items() if v is None or v == ''}

    merged = {}
    for key in ('decade', 'q', 'type', 'state'):
        if key in skip:
            continue
        if key in overrides and overrides[key] not in (None, ''):
            val = overrides[key]
            if key == 'decade' and str(val).lower() == 'all':
                continue
            merged[key] = str(val).strip()
        else:
            val = request.GET.get(key, '').strip()
            if val and not (key == 'decade' and val.lower() == 'all'):
                merged[key] = val

    if 'page' in overrides and overrides['page']:
        merged['page'] = str(int(overrides['page']))

    if not merged:
        return ''
    return urlencode(sorted(merged.items()))
