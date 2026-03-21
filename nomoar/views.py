import re
from collections import Counter
from html import escape as html_escape
from urllib.parse import quote, urlencode

from django.db import connection, transaction
from django.db.models import Count, F, Max, Min, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import DetailView, ListView, TemplateView
from django.contrib import messages

from .models import (
    ARCHIVE_EVENT_TYPE_COLORS,
    ArchiveNewsPost,
    ArchiveEventType,
    ChangeMaker,
    Collection,
    EventFistVote,
    GlossaryTerm,
    HistoricalEvent,
    LearningPath,
    LessonKit,
    LocalizedResourcePack,
    NewsletterSubscriber,
    SiteStat,
)
from .forms import EducatorNewsletterForm, EventSubmissionForm
from .related_events import combined_related_events
from .utils import map_timeline_focus_url, map_url_with_timeline_filters, timeline_params_from_map_get


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
        ctx['learning_paths'] = list(
            LearningPath.objects.filter(is_published=True).order_by('order', 'title')[:5]
        )
        ctx['commentary_posts'] = list(
            ArchiveNewsPost.objects.filter(is_published=True).order_by('-published_at')[:3]
        )
        ctx['partner_collections'] = list(
            Collection.objects.filter(
                is_published=True,
                is_partner_spotlight=True,
            ).order_by('order', 'title')[:4]
        )
        ctx['resource_packs'] = list(
            LocalizedResourcePack.objects.filter(is_published=True).order_by('order', 'title')[:4]
        )
        return ctx


class TimelineView(ListView):
    model = HistoricalEvent
    template_name = 'nomoar/timeline.html'
    context_object_name = 'events'
    paginate_by = 24

    def get_queryset(self):
        qs = HistoricalEvent.objects.prefetch_related(
            'tags', 'collections', 'sources', 'theme_labels',
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
        page_events = list(ctx.get('events') or [])
        sk = self.request.session.session_key
        fisted_ids = set()
        if sk and page_events:
            eids = [e.pk for e in page_events]
            fisted_ids = set(
                EventFistVote.objects.filter(
                    session_key=sk,
                    event_id__in=eids,
                ).values_list('event_id', flat=True),
            )
        ctx['fisted_event_ids'] = fisted_ids
        ctx['map_href_shared'] = map_url_with_timeline_filters(self.request)
        ctx['active_location'] = self.request.GET.get('location', '').strip()
        return ctx


@require_GET
def events_feed_json(request):
    """JSON list of recently updated events (for partners / educators)."""
    try:
        limit = int(request.GET.get('limit', 30))
    except ValueError:
        limit = 30
    limit = max(1, min(limit, 100))
    events = HistoricalEvent.objects.order_by('-updated_at')[:limit]
    data = [
        {
            'slug': e.slug,
            'title': e.title,
            'year': e.year,
            'summary': e.summary,
            'event_type': e.event_type,
            'state': e.state or '',
            'updated_at': e.updated_at.isoformat(),
            'url': request.build_absolute_uri(e.get_absolute_url()),
        }
        for e in events
    ]
    return JsonResponse({'events': data})


@require_GET
def oembed(request):
    """oEmbed discovery for a single event (iframe embed)."""
    url = request.GET.get('url', '').strip()
    if not url:
        return JsonResponse({'error': 'url required'}, status=400)
    m = re.search(r'EventDetail/([^/?#]+)', url, re.I)
    if not m:
        return JsonResponse({'error': 'not an event detail URL'}, status=404)
    slug = m.group(1)
    event = get_object_or_404(HistoricalEvent, slug=slug)
    embed_url = request.build_absolute_uri(reverse('nomoar:embed_event', kwargs={'slug': slug}))
    w, h = 420, 520
    title_esc = html_escape(event.title)
    iframe = (
        f'<iframe src="{html_escape(embed_url)}" width="{w}" height="{h}" '
        'style="max-width:100%;border:1px solid #333;border-radius:8px;background:#111;" '
        f'loading="lazy" title="{title_esc}"></iframe>'
    )
    return JsonResponse(
        {
            'version': '1.0',
            'type': 'rich',
            'provider_name': 'NOMOAR',
            'provider_url': request.build_absolute_uri(reverse('nomoar:home')),
            'title': event.title,
            'html': iframe,
            'width': w,
            'height': h,
        }
    )


@xframe_options_exempt
def embed_event(request, slug):
    event = get_object_or_404(
        HistoricalEvent.objects.prefetch_related('tags', 'theme_labels', 'sources'),
        slug=slug,
    )
    return render(
        request,
        'nomoar/embed_event.html',
        {
            'event': event,
            'full_site_url': request.build_absolute_uri(reverse('nomoar:event_detail', kwargs={'slug': slug})),
        },
    )


@xframe_options_exempt
def embed_slice(request):
    qs = HistoricalEvent.objects.all()
    try:
        limit = int(request.GET.get('limit', 12))
    except ValueError:
        limit = 12
    limit = max(1, min(limit, 50))
    et = request.GET.get('type', '').strip()
    if et in ArchiveEventType.values:
        qs = qs.filter(event_type=et)
    st = request.GET.get('state', '').strip().upper()
    if len(st) == 2:
        qs = qs.filter(state=st)
    qs = _apply_events_text_search(qs, request.GET.get('q', ''))
    decade = request.GET.get('decade', '').strip().lower()
    if decade and decade != 'all' and len(decade) >= 5 and decade.endswith('s') and decade[:4].isdigit():
        y = int(decade[:4])
        qs = qs.filter(year__gte=y, year__lte=y + 9)
    yf = request.GET.get('year_from', '').strip()
    yt = request.GET.get('year_to', '').strip()
    if yf.isdigit():
        qs = qs.filter(year__gte=int(yf))
    if yt.isdigit():
        qs = qs.filter(year__lte=int(yt))
    loc = request.GET.get('location', '').strip()
    if loc:
        qs = qs.filter(location=loc)
    events = list(qs.order_by('-year', 'title')[:limit])
    events_with_urls = [(e, request.build_absolute_uri(e.get_absolute_url())) for e in events]
    return render(
        request,
        'nomoar/embed_slice.html',
        {
            'events_with_urls': events_with_urls,
            'full_timeline_url': request.build_absolute_uri(reverse('nomoar:timeline')),
        },
    )


@require_POST
def toggle_event_fist(request, slug):
    """Toggle this session's raised-fist for an event (+1 / -1 on aggregate count)."""
    event = get_object_or_404(HistoricalEvent, slug=slug)
    if not request.session.session_key:
        request.session.save()
    sk = request.session.session_key
    if not sk:
        return JsonResponse({'ok': False, 'error': 'session'}, status=400)

    with transaction.atomic():
        ev = HistoricalEvent.objects.select_for_update().get(pk=event.pk)
        vote = EventFistVote.objects.filter(event=ev, session_key=sk).first()
        if vote:
            vote.delete()
            HistoricalEvent.objects.filter(pk=ev.pk, raised_fists__gt=0).update(
                raised_fists=F('raised_fists') - 1,
            )
            user_has = False
        else:
            EventFistVote.objects.create(event=ev, session_key=sk)
            HistoricalEvent.objects.filter(pk=ev.pk).update(
                raised_fists=F('raised_fists') + 1,
            )
            user_has = True
    ev.refresh_from_db()
    return JsonResponse(
        {
            'ok': True,
            'raised_fists': ev.raised_fists,
            'user_has_fisted': user_has,
        },
    )


class EventDetailView(DetailView):
    model = HistoricalEvent
    template_name = 'nomoar/event_detail.html'
    context_object_name = 'event'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return HistoricalEvent.objects.prefetch_related(
            'sources',
            'tags',
            'collections',
            'theme_labels',
            'curated_related',
            'glossary_terms',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        req = self.request
        sk = req.session.session_key
        evt = ctx['event']
        ctx['user_has_fisted'] = (
            bool(sk)
            and EventFistVote.objects.filter(event=evt, session_key=sk).exists()
        )
        ctx['related_events_list'] = combined_related_events(evt, limit=8)
        ctx['embed_event_url'] = req.build_absolute_uri(
            reverse('nomoar:embed_event', kwargs={'slug': evt.slug}),
        )
        ctx['embed_iframe_code'] = (
            f'<iframe src="{html_escape(ctx["embed_event_url"])}" width="420" height="520" '
            'style="max-width:100%;border:1px solid #333;border-radius:8px;" '
            f'title="{html_escape(evt.title)}" loading="lazy"></iframe>'
        )
        slice_base = req.build_absolute_uri(reverse('nomoar:embed_slice'))
        ctx['embed_slice_example_url'] = f'{slice_base}?limit=10'
        canon = req.build_absolute_uri(evt.get_absolute_url())
        ctx['event_canonical_url'] = canon
        ctx['event_canonical_url_quoted'] = quote(canon, safe='')
        ctx['oembed_json_url'] = (
            req.build_absolute_uri(reverse('nomoar:oembed'))
            + f'?format=json&url={ctx["event_canonical_url_quoted"]}'
        )
        ctx['rss_feed_url'] = req.build_absolute_uri(reverse('nomoar:events_feed_rss'))
        ctx['json_feed_url'] = req.build_absolute_uri(reverse('nomoar:events_feed_json'))
        ctx['map_href_shared'] = map_url_with_timeline_filters(req, focus=evt.slug)
        ctx['glossary_for_event'] = list(evt.glossary_terms.all())
        ctx['event_collections_published'] = list(evt.collections.filter(is_published=True))
        return ctx


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
        st_map = req.get('state', '').strip().upper()
        if st_map and len(st_map) == 2:
            qs = qs.filter(state=st_map)
        else:
            st_map = ''
        loc_map = req.get('location', '').strip()
        if loc_map:
            qs = qs.filter(location=loc_map)
        else:
            loc_map = ''

        mapped = []
        for e in qs:
            color = ARCHIVE_EVENT_TYPE_COLORS.get(e.event_type, '#1e88e5')
            tf_url = map_timeline_focus_url(e.slug, self.request)
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
        ctx['map_state'] = st_map
        ctx['map_location'] = loc_map
        ctx['map_states'] = list(
            HistoricalEvent.objects.exclude(state='')
            .values_list('state', flat=True)
            .distinct()
            .order_by('state'),
        )
        loc_rows = base_qs.exclude(location='').values_list('location', flat=True)
        loc_counts = Counter(loc_rows)
        ctx['map_top_locations'] = loc_counts.most_common(60)
        ctx['map_event_type_choices'] = ArchiveEventType.choices
        ctx['map_filters_active'] = bool(
            ctx['map_q']
            or ctx['map_year_from']
            or ctx['map_year_to']
            or ctx['map_type']
            or ctx['map_state']
            or ctx['map_location'],
        )
        tparams = timeline_params_from_map_get(req)
        ctx['timeline_href_shared'] = reverse('nomoar:timeline') + (
            '?' + urlencode(sorted(tparams.items())) if tparams else ''
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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        req = self.request
        ctx['lesson_kits'] = list(
            LessonKit.objects.filter(is_published=True).order_by('order', 'title')[:12]
        )
        ctx['learning_paths'] = list(
            LearningPath.objects.filter(is_published=True).order_by('order', 'title')[:12]
        )
        ctx['resource_packs'] = list(
            LocalizedResourcePack.objects.filter(is_published=True).order_by('order', 'title')[:12]
        )
        ctx['partner_collections'] = list(
            Collection.objects.filter(
                is_published=True,
                is_partner_spotlight=True,
            ).order_by('order', 'title')[:8]
        )
        ctx['newsletter_form'] = EducatorNewsletterForm()
        ctx['rss_feed_url'] = req.build_absolute_uri(reverse('nomoar:events_feed_rss'))
        ctx['json_feed_url'] = req.build_absolute_uri(reverse('nomoar:events_feed_json'))
        return ctx


class PricingView(TemplateView):
    template_name = 'nomoar/pricing.html'


@require_POST
def subscribe_educator_newsletter(request):
    form = EducatorNewsletterForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        obj, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={'active': True},
        )
        if not created:
            if not obj.active:
                obj.active = True
                obj.save(update_fields=['active'])
        messages.success(
            request,
            'Thanks — you’re on the educator digest list. '
            'We’ll only use this for updates; you can also subscribe via RSS or JSON anytime.',
        )
    else:
        messages.error(request, 'Please enter a valid email address.')
    return redirect('nomoar:educators')


class LearningPathListView(ListView):
    model = LearningPath
    template_name = 'nomoar/learning_path_list.html'
    context_object_name = 'paths'

    def get_queryset(self):
        return LearningPath.objects.filter(is_published=True).order_by('order', 'title')


class LearningPathDetailView(DetailView):
    model = LearningPath
    template_name = 'nomoar/learning_path_detail.html'
    context_object_name = 'path'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return (
            LearningPath.objects.filter(is_published=True)
            .prefetch_related('steps__event__tags', 'steps__event__theme_labels')
        )


class CollectionListView(ListView):
    model = Collection
    template_name = 'nomoar/collection_list.html'
    context_object_name = 'collections'

    def get_queryset(self):
        return Collection.objects.filter(is_published=True).order_by('order', 'title')


class CollectionDetailView(DetailView):
    model = Collection
    template_name = 'nomoar/collection_detail.html'
    context_object_name = 'collection'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Collection.objects.filter(is_published=True).prefetch_related(
            'events__tags',
            'events__theme_labels',
        )


class LessonKitListView(ListView):
    model = LessonKit
    template_name = 'nomoar/lesson_kit_list.html'
    context_object_name = 'kits'

    def get_queryset(self):
        return LessonKit.objects.filter(is_published=True).select_related('related_path').order_by(
            'order', 'title'
        )


class LessonKitDetailView(DetailView):
    model = LessonKit
    template_name = 'nomoar/lesson_kit_detail.html'
    context_object_name = 'kit'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return LessonKit.objects.filter(is_published=True).select_related('related_path')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        k = ctx['kit']
        ctx['embed_slice_url'] = self.request.build_absolute_uri(reverse('nomoar:embed_slice'))
        if k.related_path_id:
            ctx['related_path'] = k.related_path
        return ctx


class WhatsNewView(ListView):
    """Recently created or updated archive entries (digest-friendly)."""
    model = HistoricalEvent
    template_name = 'nomoar/whats_new.html'
    context_object_name = 'events'
    paginate_by = 30

    def get_queryset(self):
        return HistoricalEvent.objects.order_by('-updated_at').prefetch_related('tags', 'theme_labels')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['rss_feed_url'] = self.request.build_absolute_uri(reverse('nomoar:events_feed_rss'))
        ctx['json_feed_url'] = self.request.build_absolute_uri(reverse('nomoar:events_feed_json'))
        return ctx


class GlossaryListView(ListView):
    model = GlossaryTerm
    template_name = 'nomoar/glossary_list.html'
    context_object_name = 'terms'

    def get_queryset(self):
        return GlossaryTerm.objects.all().order_by('order', 'title')


class GlossaryTermDetailView(DetailView):
    model = GlossaryTerm
    template_name = 'nomoar/glossary_term_detail.html'
    context_object_name = 'term'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return GlossaryTerm.objects.prefetch_related(
            'related_events__tags',
            'related_events__theme_labels',
        )


class PlaceIndexView(TemplateView):
    template_name = 'nomoar/place_index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rows = (
            HistoricalEvent.objects.exclude(location='')
            .values('location', 'state')
            .annotate(event_count=Count('id'))
            .order_by('-event_count', 'location')[:400]
        )
        ctx['places'] = list(rows)
        return ctx


class NewsPostListView(ListView):
    model = ArchiveNewsPost
    template_name = 'nomoar/news_post_list.html'
    context_object_name = 'posts'
    paginate_by = 20

    def get_queryset(self):
        return ArchiveNewsPost.objects.filter(is_published=True).prefetch_related(
            'related_events',
        ).order_by('-published_at')


class NewsPostDetailView(DetailView):
    model = ArchiveNewsPost
    template_name = 'nomoar/news_post_detail.html'
    context_object_name = 'post'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return ArchiveNewsPost.objects.filter(is_published=True).prefetch_related(
            'related_events',
        )


class ResourcePackListView(ListView):
    model = LocalizedResourcePack
    template_name = 'nomoar/resource_pack_list.html'
    context_object_name = 'packs'

    def get_queryset(self):
        return LocalizedResourcePack.objects.filter(is_published=True).order_by('order', 'title')


class ResourcePackDetailView(DetailView):
    model = LocalizedResourcePack
    template_name = 'nomoar/resource_pack_detail.html'
    context_object_name = 'pack'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return LocalizedResourcePack.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        p = ctx['pack']
        ctx['embed_slice_url'] = self.request.build_absolute_uri(reverse('nomoar:embed_slice'))
        ctx['timeline_location_url'] = ''
        if p.city:
            ctx['timeline_location_url'] = reverse('nomoar:timeline') + '?' + urlencode(
                {'location': p.city}
            )
        return ctx


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
