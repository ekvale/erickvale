"""Related archive entries: manual curation + tag / state / decade overlap."""
from django.db.models import Count, Q

from .models import HistoricalEvent


def combined_related_events(event: HistoricalEvent, limit: int = 8):
    """
    Return up to `limit` other events: curated first, then tag overlap,
    same state, same decade (year // 10). De-duplicated, excludes self.
    """
    if limit <= 0:
        return []
    out = []
    seen = {event.pk}

    for e in event.curated_related.all():
        if e.pk in seen:
            continue
        out.append(e)
        seen.add(e.pk)
        if len(out) >= limit:
            return out

    need = limit - len(out)
    tag_ids = list(event.tags.values_list('pk', flat=True))
    decade_lo = (event.year // 10) * 10
    decade_hi = decade_lo + 9

    base = HistoricalEvent.objects.exclude(pk__in=seen)

    if tag_ids and need > 0:
        tagged = (
            base.filter(tags__pk__in=tag_ids)
            .annotate(
                tag_overlap=Count(
                    'tags',
                    filter=Q(tags__pk__in=tag_ids),
                    distinct=True,
                ),
            )
            .distinct()
            .order_by('-tag_overlap', '-year', 'title')
        )
        for e in tagged[: need + 8]:
            if e.pk in seen:
                continue
            out.append(e)
            seen.add(e.pk)
            if len(out) >= limit:
                return out
            need = limit - len(out)

    if event.state and need > 0:
        for e in base.filter(state=event.state).order_by('-year', 'title'):
            if e.pk in seen:
                continue
            out.append(e)
            seen.add(e.pk)
            if len(out) >= limit:
                return out
            need = limit - len(out)

    if need > 0:
        for e in (
            base.filter(year__gte=decade_lo, year__lte=decade_hi)
            .order_by('-year', 'title')
        ):
            if e.pk in seen:
                continue
            out.append(e)
            seen.add(e.pk)
            if len(out) >= limit:
                break

    return out[:limit]
