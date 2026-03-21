"""Timeline / map shared GET filter logic (year range, decade, location, tag, theme, type, state)."""
from django.db.models import QuerySet

from .models import ArchiveEventType, HistoricalEvent


def filter_events_by_timeline_get(qs: QuerySet, get) -> QuerySet:
    """
    Apply URL filter params to a HistoricalEvent queryset.
    Precedence: if year_from or year_to is set, decade/single year are ignored for range.
    """
    yf_raw = get.get('year_from', '').strip()
    yt_raw = get.get('year_to', '').strip()
    use_range = yf_raw.isdigit() or yt_raw.isdigit()

    if use_range:
        if yf_raw.isdigit():
            qs = qs.filter(year__gte=int(yf_raw))
        if yt_raw.isdigit():
            qs = qs.filter(year__lte=int(yt_raw))
    else:
        decade = get.get('decade', '').strip().lower()
        decade_ok = False
        if decade and decade != 'all':
            if len(decade) >= 5 and decade.endswith('s') and decade[:4].isdigit():
                start = int(decade[:4])
                qs = qs.filter(year__gte=start, year__lte=start + 9)
                decade_ok = True
        if not decade_ok:
            y = get.get('year')
            if y and str(y).isdigit():
                qs = qs.filter(year=int(y))

    et = get.get('type', '').strip()
    if et and et in ArchiveEventType.values:
        qs = qs.filter(event_type=et)

    st = get.get('state', '').strip().upper()
    if st and len(st) == 2:
        qs = qs.filter(state=st)

    loc = get.get('location', '').strip()
    if loc:
        qs = qs.filter(location=loc)

    tag_slug = get.get('tag', '').strip()
    if tag_slug:
        qs = qs.filter(tags__slug=tag_slug)

    theme_slug = get.get('theme', '').strip()
    if theme_slug:
        qs = qs.filter(theme_labels__slug=theme_slug)

    if tag_slug or theme_slug:
        qs = qs.distinct()
    return qs
