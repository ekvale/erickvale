"""Full-text search + optional highlighted snippets for timeline cards."""
import re

from django.db import connection
from django.db.models import Q, QuerySet
from django.utils.html import escape
from django.utils.safestring import SafeString, mark_safe

from .models import HistoricalEvent


def apply_events_text_search(qs: QuerySet[HistoricalEvent], q_raw: str) -> QuerySet[HistoricalEvent]:
    """Full-text on Postgres; icontains fallback (no snippet annotation)."""
    q = (q_raw or '').strip()
    if not q:
        return qs
    if connection.vendor == 'postgresql':
        from django.contrib.postgres.search import SearchQuery, SearchVector

        vector = (
            SearchVector('title', weight='A')
            + SearchVector('summary', weight='B')
            + SearchVector('body', weight='C')
        )
        return qs.annotate(search=vector).filter(
            search=SearchQuery(q, config='english', search_type='plain'),
        )
    return qs.filter(
        Q(title__icontains=q) | Q(summary__icontains=q) | Q(body__icontains=q),
    )


def apply_events_text_search_with_headline(
    qs: QuerySet[HistoricalEvent],
    q_raw: str,
) -> QuerySet[HistoricalEvent]:
    """Postgres: filter + SearchHeadline on summary. Other DBs: icontains only."""
    q = (q_raw or '').strip()
    if not q:
        return qs
    if connection.vendor == 'postgresql':
        from django.contrib.postgres.search import SearchHeadline, SearchQuery, SearchVector

        vector = (
            SearchVector('title', weight='A')
            + SearchVector('summary', weight='B')
            + SearchVector('body', weight='C')
        )
        sq = SearchQuery(q, config='english', search_type='plain')
        return (
            qs.annotate(search=vector)
            .filter(search=sq)
            .annotate(
                search_snippet=SearchHeadline(
                    'summary',
                    sq,
                    config='english',
                    start_sel='<mark class="nomoar-search-hit">',
                    stop_sel='</mark>',
                    max_words=48,
                    min_words=8,
                ),
            )
        )
    return qs.filter(
        Q(title__icontains=q) | Q(summary__icontains=q) | Q(body__icontains=q),
    )


def highlight_terms_html(text: str, query: str, max_length: int = 260) -> SafeString:
    """Escape text, wrap query tokens in <mark> (case-insensitive). Fallback for SQLite / empty headlines."""
    text = escape((text or '').strip())
    q = (query or '').strip()
    if not text or not q:
        return mark_safe(text)
    terms = [t for t in re.split(r'\s+', q) if len(t) >= 2]
    if not terms:
        return mark_safe(text[:max_length] + ('…' if len(text) > max_length else ''))
    try:
        pattern = '|'.join(re.escape(t) for t in terms)

        def repl(m):
            return f'<mark class="nomoar-search-hit">{m.group(0)}</mark>'

        out = re.sub(f'({pattern})', repl, text, flags=re.IGNORECASE)
    except re.error:
        out = text
    if len(out) > max_length:
        out = out[: max_length - 1] + '…'
    return mark_safe(out)


def attach_search_snippet_display(events, q_raw: str) -> None:
    """
    Mutate event instances in place: set search_snippet_display (SafeString) for templates.
    Use after pagination when not using Postgres headline or headline is empty.
    """
    q = (q_raw or '').strip()
    if not q:
        return
    for e in events:
        raw = getattr(e, 'search_snippet', None)
        if raw:
            e.search_snippet_display = mark_safe(raw)
        else:
            blob = (e.summary or '') or (e.title or '')
            e.search_snippet_display = highlight_terms_html(blob, q)
