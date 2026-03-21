"""Shared helpers for NOMOAR views and templates."""
from urllib.parse import urlencode


def timeline_filter_querystring(request, **overrides):
    """
    Build query string for timeline filters.
    Keys: decade, q, type, state, location, year_from, year_to, tag, theme, focus.
    Pass key='' or None to remove from output (e.g. decade='' for All Time, year_from='' to clear range).
    Page is only added when passed explicitly in overrides (not copied from request).
    """
    skip = {k for k, v in overrides.items() if v is None or v == ''}

    merged = {}
    for key in (
        'decade',
        'q',
        'type',
        'state',
        'location',
        'year_from',
        'year_to',
        'tag',
        'theme',
        'focus',
    ):
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


def map_filter_querystring(request, **overrides):
    """
    Build query string for map filters.
    Keys: year_from, year_to, type, state, q, focus, location, tag, theme.
    Pass key='' or None to drop.
    """
    skip = {k for k, v in overrides.items() if v is None or v == ''}
    merged = {}
    for key in ('year_from', 'year_to', 'type', 'state', 'q', 'focus', 'location', 'tag', 'theme'):
        if key in skip:
            continue
        if key in overrides and overrides[key] not in (None, ''):
            merged[key] = str(overrides[key]).strip()
        else:
            val = request.GET.get(key, '').strip()
            if val:
                merged[key] = val
    if not merged:
        return ''
    return urlencode(sorted(merged.items()))


def timeline_params_from_map_get(get) -> dict:
    """Map query → timeline query dict (type, state, q, decade or year, tag, theme, year range)."""
    out = {}
    for key in ('type', 'state', 'q', 'tag', 'theme'):
        v = get.get(key, '').strip()
        if v:
            out[key] = v
    yf = get.get('year_from', '').strip()
    yt = get.get('year_to', '').strip()
    if yf.isdigit():
        out['year_from'] = yf
    if yt.isdigit():
        out['year_to'] = yt
    if yf.isdigit() and yt.isdigit():
        yfi, yti = int(yf), int(yt)
        if yfi == yti:
            out['year'] = str(yfi)
            out.pop('year_from', None)
            out.pop('year_to', None)
        elif yfi // 10 == yti // 10 and yti - yfi == 9 and yfi % 10 == 0:
            out['decade'] = f'{yfi}s'
            out.pop('year_from', None)
            out.pop('year_to', None)
    return out


def map_params_from_timeline_get(get) -> dict:
    """Timeline query → map query dict (type, state, q, year_from/to, focus, location, tag, theme)."""
    out = {}
    for key in ('type', 'state', 'q', 'focus', 'location', 'tag', 'theme'):
        v = get.get(key, '').strip()
        if v:
            out[key] = v
    yf_raw = get.get('year_from', '').strip()
    yt_raw = get.get('year_to', '').strip()
    if yf_raw.isdigit():
        out['year_from'] = yf_raw
    if yt_raw.isdigit():
        out['year_to'] = yt_raw
    use_range = yf_raw.isdigit() or yt_raw.isdigit()
    if not use_range:
        dec = get.get('decade', '').strip().lower()
        if dec and dec != 'all' and len(dec) >= 5 and dec.endswith('s') and dec[:4].isdigit():
            y = int(dec[:4])
            out['year_from'] = str(y)
            out['year_to'] = str(y + 9)
        y_one = get.get('year', '').strip()
        if y_one.isdigit() and 'year_from' not in out and 'year_to' not in out:
            y = int(y_one)
            out['year_from'] = str(y)
            out['year_to'] = str(y)
    return out


def map_url_with_timeline_filters(request, **extra) -> str:
    from django.urls import reverse

    base = reverse('nomoar:map')
    params = map_params_from_timeline_get(request.GET)
    params.update({k: v for k, v in extra.items() if v not in (None, '')})
    qs = urlencode(sorted((k, str(v)) for k, v in params.items() if v not in (None, '')))
    return f'{base}?{qs}' if qs else base


def map_timeline_focus_url(slug: str, request) -> str:
    """Timeline URL with current map filters + focus=slug."""
    from django.urls import reverse

    base = reverse('nomoar:timeline')
    params = timeline_params_from_map_get(request.GET)
    params['focus'] = slug
    qs = urlencode(sorted((k, v) for k, v in params.items() if v))
    return f'{base}?{qs}' if qs else f'{base}?focus={slug}'
