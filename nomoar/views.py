from django.db import connection
from django.db.models import Count, Max, Min, Q
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView
from django.contrib import messages

from .models import (
    ARCHIVE_EVENT_TYPE_COLORS,
    ArchiveEventType,
    ChangeMaker,
    Collection,
    HistoricalEvent,
    SiteStat,
)
from .forms import EventSubmissionForm


def _apply_events_text_search(qs, q_raw):
    """Full-text on Postgres (plain query); icontains fallback elsewhere."""
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
            search=SearchQuery(
                q,
                config='english',
                search_type='plain',
            ),
        )
    return qs.filter(
        Q(title__icontains=q)
        | Q(summary__icontains=q)
        | Q(body__icontains=q),
    )


class HomeView(TemplateView):
    template_name = 'nomoar/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['recent_events'] = HistoricalEvent.objects.all()[:6]
        ctx['stats'] = {s.key: s for s in SiteStat.objects.all()}
        ctx['event_count'] = HistoricalEvent.objects.count()
        ctx['state_count'] = (
            HistoricalEvent.objects.exclude(state='')
            .values('state')
            .distinct()
            .count()
        )
        fe = list(HistoricalEvent.objects.filter(featured=True)[:6])
        if not fe:
            fe = list(HistoricalEvent.objects.all()[:6])
        ctx['featured_events'] = fe
        ctx['heroes_preview'] = list(
            ChangeMaker.objects.filter(is_published=True).order_by('order', 'name')[:4]
        )
        return ctx


class TimelineView(ListView):
    model = HistoricalEvent
    template_name = 'nomoar/timeline.html'
    context_object_name = 'events'
    paginate_by = 24

    def get_queryset(self):
        qs = HistoricalEvent.objects.prefetch_related(
            'tags', 'collections', 'sources',
        )
        y = self.request.GET.get('year')
        if y and y.isdigit():
            qs = qs.filter(year=int(y))
        qs = _apply_events_text_search(qs, self.request.GET.get('q', ''))
        decade = self.request.GET.get('decade', '').strip().lower()
        if decade and decade != 'all':
            if len(decade) >= 5 and decade.endswith('s') and decade[:4].isdigit():
                start = int(decade[:4])
                qs = qs.filter(year__gte=start, year__lte=start + 9)
        et = self.request.GET.get('type', '').strip()
        if et and et in ArchiveEventType.values:
            qs = qs.filter(event_type=et)
        st = self.request.GET.get('state', '').strip().upper()
        if st and len(st) == 2:
            qs = qs.filter(state=st)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['decade_options'] = [
            ('all', 'All Time'),
            ('2020s', '2020s'),
            ('2010s', '2010s'),
            ('2000s', '2000s'),
            ('1990s', '1990s'),
            ('1980s', '1980s'),
            ('1970s', '1970s'),
            ('1960s', '1960s'),
            ('1950s', '1950s'),
            ('1940s', '1940s'),
            ('1930s', '1930s'),
            ('1920s', '1920s'),
            ('1910s', '1910s'),
            ('1900s', '1900s'),
        ]
        ctx['active_decade'] = self.request.GET.get('decade', 'all').strip().lower() or 'all'
        ctx['active_type'] = self.request.GET.get('type', '').strip()
        ctx['active_state'] = self.request.GET.get('state', '').strip().upper()
        ctx['focus_slug'] = self.request.GET.get('focus', '').strip()
        ctx['event_type_choices'] = ArchiveEventType.choices
        ctx['timeline_states'] = list(
            HistoricalEvent.objects.exclude(state='')
            .values_list('state', flat=True)
            .distinct()
            .order_by('state'),
        )
        return ctx


class EventDetailView(DetailView):
    model = HistoricalEvent
    template_name = 'nomoar/event_detail.html'
    context_object_name = 'event'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return HistoricalEvent.objects.prefetch_related(
            'sources', 'tags', 'collections',
        )


class MapView(TemplateView):
    template_name = 'nomoar/map.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['events_with_state'] = (
            HistoricalEvent.objects.exclude(state='')
            .values('state')
            .annotate(n=Count('id'))
            .order_by('-n')
        )
        base_qs = HistoricalEvent.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
        )
        ctx['map_geocoded_count'] = base_qs.count()
        bounds = base_qs.aggregate(y_min=Min('year'), y_max=Max('year'))
        ctx['map_year_hint_min'] = bounds['y_min']
        ctx['map_year_hint_max'] = bounds['y_max']

        req = self.request.GET
        qs = base_qs.order_by('-year', 'title')
        yf_raw = req.get('year_from', '').strip()
        yt_raw = req.get('year_to', '').strip()
        if yf_raw.isdigit():
            qs = qs.filter(year__gte=int(yf_raw))
        if yt_raw.isdigit():
            qs = qs.filter(year__lte=int(yt_raw))
        et = req.get('type', '').strip()
        if et and et in ArchiveEventType.values:
            qs = qs.filter(event_type=et)
        else:
            et = ''
        qs = _apply_events_text_search(qs, req.get('q', ''))

        mapped = []
        for e in qs:
            color = ARCHIVE_EVENT_TYPE_COLORS.get(e.event_type, '#1e88e5')
            tf_url = reverse('nomoar:timeline') + '?focus=' + e.slug
            mapped.append(
                {
                    'slug': e.slug,
                    'title': e.title,
                    'year': e.year,
                    'summary': e.summary[:400] + ('…' if len(e.summary) > 400 else ''),
                    'location': e.location or '',
                    'state': e.state or '',
                    'lat': float(e.latitude),
                    'lng': float(e.longitude),
                    'type': e.event_type,
                    'type_label': e.get_event_type_display(),
                    'color': color,
                    'url': reverse('nomoar:event_detail', kwargs={'slug': e.slug}),
                    'timeline_focus_url': tf_url,
                },
            )
        ctx['map_events'] = mapped
        ctx['map_focus_slug'] = req.get('focus', '').strip()
        ctx['map_q'] = req.get('q', '').strip()
        ctx['map_year_from'] = yf_raw if yf_raw.isdigit() else ''
        ctx['map_year_to'] = yt_raw if yt_raw.isdigit() else ''
        ctx['map_type'] = et
        ctx['map_event_type_choices'] = ArchiveEventType.choices
        ctx['map_filters_active'] = bool(
            ctx['map_q']
            or ctx['map_year_from']
            or ctx['map_year_to']
            or ctx['map_type'],
        )
        ctx['legend_types'] = [
            {
                'slug': c.value,
                'label': c.label,
                'color': ARCHIVE_EVENT_TYPE_COLORS[c],
            }
            for c in ArchiveEventType
        ]
        return ctx


def submit_event(request):
    if request.method == 'POST':
        form = EventSubmissionForm(request.POST)
        if form.is_valid():
            messages.success(
                request,
                'Thank you. Your submission has been received for review. '
                'This archive is maintained independently of nomoar.org.',
            )
            form = EventSubmissionForm()
    else:
        form = EventSubmissionForm()
    return render(request, 'nomoar/submit.html', {'form': form})


class EducatorsView(TemplateView):
    template_name = 'nomoar/educators.html'


class PricingView(TemplateView):
    template_name = 'nomoar/pricing.html'


class HeroesView(ListView):
    model = ChangeMaker
    template_name = 'nomoar/heroes.html'
    context_object_name = 'heroes'

    def get_queryset(self):
        return ChangeMaker.objects.filter(is_published=True).order_by('order', 'name')


class HeroDetailView(DetailView):
    model = ChangeMaker
    template_name = 'nomoar/hero_detail.html'
    context_object_name = 'hero'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return (
            ChangeMaker.objects.filter(is_published=True)
            .prefetch_related('related_events')
        )
