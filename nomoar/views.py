from django.shortcuts import render
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib import messages
from django.db.models import Count, Q
from django.urls import reverse

from .models import (
    ARCHIVE_EVENT_TYPE_COLORS,
    ArchiveEventType,
    Collection,
    HistoricalEvent,
    SiteStat,
)
from .forms import EventSubmissionForm


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
        return ctx


class TimelineView(ListView):
    model = HistoricalEvent
    template_name = 'nomoar/timeline.html'
    context_object_name = 'events'
    paginate_by = 20

    def get_queryset(self):
        qs = HistoricalEvent.objects.all()
        y = self.request.GET.get('year')
        if y and y.isdigit():
            qs = qs.filter(year=int(y))
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(summary__icontains=q))
        return qs


class EventDetailView(DetailView):
    model = HistoricalEvent
    template_name = 'nomoar/event_detail.html'
    context_object_name = 'event'
    slug_url_kwarg = 'slug'


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
        mapped = []
        # Use __isnull=False — exclude(field=None) can miss rows on some DB/backends for FloatField
        qs = HistoricalEvent.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
        ).order_by('-year', 'title')
        for e in qs:
            color = ARCHIVE_EVENT_TYPE_COLORS.get(e.event_type, '#1e88e5')
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
                }
            )
        ctx['map_events'] = mapped
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
