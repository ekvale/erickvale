"""Related paths, glossary, heroes, and commentary for detail pages."""
from django.db.models import Q

from .models import (
    ArchiveNewsPost,
    ChangeMaker,
    GlossaryTerm,
    HistoricalEvent,
    LearningPath,
)


def event_ids_from_queryset_or_list(events) -> list[int]:
    return [e.pk if hasattr(e, 'pk') else int(e) for e in events]


def learning_paths_for_events(
    event_ids: list[int],
    *,
    exclude_path_pk: int | None = None,
    limit: int = 8,
):
    if not event_ids:
        return LearningPath.objects.none()
    qs = (
        LearningPath.objects.filter(is_published=True, steps__event_id__in=event_ids)
        .distinct()
        .order_by('order', 'title')
    )
    if exclude_path_pk:
        qs = qs.exclude(pk=exclude_path_pk)
    return qs[:limit]


def glossary_terms_for_events(
    event_ids: list[int],
    *,
    exclude_term_pk: int | None = None,
    limit: int = 10,
):
    if not event_ids:
        return GlossaryTerm.objects.none()
    qs = GlossaryTerm.objects.filter(related_events__in=event_ids).distinct().order_by('order', 'title')
    if exclude_term_pk:
        qs = qs.exclude(pk=exclude_term_pk)
    return qs[:limit]


def heroes_for_events(
    event_ids: list[int],
    *,
    exclude_hero_pk: int | None = None,
    limit: int = 8,
):
    if not event_ids:
        return ChangeMaker.objects.none()
    qs = (
        ChangeMaker.objects.filter(is_published=True, related_events__in=event_ids)
        .distinct()
        .order_by('order', 'name')
    )
    if exclude_hero_pk:
        qs = qs.exclude(pk=exclude_hero_pk)
    return qs[:limit]


def news_posts_for_events(
    event_ids: list[int],
    *,
    exclude_post_pk: int | None = None,
    limit: int = 6,
):
    if not event_ids:
        return ArchiveNewsPost.objects.none()
    qs = (
        ArchiveNewsPost.objects.filter(is_published=True, related_events__in=event_ids)
        .distinct()
        .order_by('-published_at')
    )
    if exclude_post_pk:
        qs = qs.exclude(pk=exclude_post_pk)
    return qs[:limit]


def events_related_to_glossary_term(
    term: GlossaryTerm,
    *,
    exclude_slugs: set | None = None,
    limit: int = 12,
):
    """Extra events that share tags/theme with term's related events (not already linked)."""
    related = list(term.related_events.all())
    if not related:
        return HistoricalEvent.objects.none()
    base_ids = {e.pk for e in related}
    tag_ids = set()
    theme_ids = set()
    for e in related:
        tag_ids.update(e.tags.values_list('pk', flat=True))
        theme_ids.update(e.theme_labels.values_list('pk', flat=True))
    q = Q()
    if tag_ids:
        q |= Q(tags__in=tag_ids)
    if theme_ids:
        q |= Q(theme_labels__in=theme_ids)
    if not q:
        return HistoricalEvent.objects.none()
    qs = (
        HistoricalEvent.objects.filter(q)
        .exclude(pk__in=base_ids)
        .distinct()
        .order_by('-year', 'title')
    )
    if exclude_slugs:
        qs = qs.exclude(slug__in=exclude_slugs)
    return qs[:limit]
