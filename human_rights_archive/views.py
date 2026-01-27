"""Views for Human Rights & Constitutional Violations Archive."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
import csv
from datetime import datetime

from .models import Source, Article, Tag, FeedFetchLog
from .forms import ArticleFilterForm, AddByUrlForm


@staff_member_required
def dashboard(request):
    """Dashboard with stats and recent articles."""
    total_articles = Article.objects.count()
    total_sources = Source.objects.filter(is_active=True).count()
    total_tags = Tag.objects.count()
    recent_articles = Article.objects.select_related('source').prefetch_related('tags').order_by('-fetched_at')[:10]
    recent_feeds = Source.objects.filter(is_active=True).order_by('-last_fetched')[:5]
    articles_by_tag = Tag.objects.annotate(num=Count('articles')).order_by('-num')[:10]
    context = {
        'total_articles': total_articles,
        'total_sources': total_sources,
        'total_tags': total_tags,
        'recent_articles': recent_articles,
        'recent_feeds': recent_feeds,
        'articles_by_tag': articles_by_tag,
    }
    return render(request, 'human_rights_archive/dashboard.html', context)


@staff_member_required
def article_list(request):
    """List articles with search and filters."""
    qs = Article.objects.select_related('source').prefetch_related('tags').order_by('-published_at', '-fetched_at')
    form = ArticleFilterForm(request.GET or None)
    if form.is_valid():
        q = form.cleaned_data.get('q', '').strip()
        if q:
            vector = SearchVector('title', weight='A', config='english') + SearchVector('summary', weight='B', config='english') + SearchVector('content', weight='C', config='english')
            query = SearchQuery(q, config='english')
            qs = qs.annotate(rank=SearchRank(vector, query)).filter(rank__gt=0).order_by('-rank', '-published_at')
        tags = form.cleaned_data.get('tags')
        if tags:
            qs = qs.filter(tags__in=tags).distinct()
        source = form.cleaned_data.get('source')
        if source:
            qs = qs.filter(source=source)
        date_from = form.cleaned_data.get('date_from')
        if date_from:
            qs = qs.filter(published_at__date__gte=date_from)
        date_to = form.cleaned_data.get('date_to')
        if date_to:
            qs = qs.filter(published_at__date__lte=date_to)
    else:
        form = ArticleFilterForm()
    paginator = Paginator(qs, 20)
    page = request.GET.get('page', 1)
    articles = paginator.get_page(page)
    context = {'articles': articles, 'form': form}
    return render(request, 'human_rights_archive/article_list.html', context)


@staff_member_required
def article_detail(request, pk):
    """Article detail view."""
    article = get_object_or_404(Article.objects.select_related('source').prefetch_related('tags'), pk=pk)
    return render(request, 'human_rights_archive/article_detail.html', {'article': article})


@staff_member_required
def source_list(request):
    """List and manage sources/feeds."""
    sources = Source.objects.prefetch_related('default_tags').annotate(
        article_count=Count('articles')
    ).order_by('name')
    return render(request, 'human_rights_archive/source_list.html', {'sources': sources})


@staff_member_required
def tag_list(request):
    """List tags with counts."""
    tags = Tag.objects.annotate(article_count=Count('articles')).order_by('category', 'name')
    return render(request, 'human_rights_archive/tag_list.html', {'tags': tags})


@staff_member_required
def about(request):
    """About the archive."""
    return render(request, 'human_rights_archive/about.html')


@staff_member_required
def export_csv(request):
    """Export filtered articles to CSV. Use same query params as article list for consistency."""
    qs = Article.objects.select_related('source').prefetch_related('tags').order_by('-published_at')
    form = ArticleFilterForm(request.GET or None)
    # Preserve current list filters when exporting: use request.GET
    if form.is_valid():
        q = form.cleaned_data.get('q', '').strip()
        if q:
            vector = SearchVector('title', weight='A', config='english') + SearchVector('summary', weight='B', config='english') + SearchVector('content', weight='C', config='english')
            query = SearchQuery(q, config='english')
            qs = qs.annotate(rank=SearchRank(vector, query)).filter(rank__gt=0).order_by('-rank', '-published_at')
        tags = form.cleaned_data.get('tags')
        if tags:
            qs = qs.filter(tags__in=tags).distinct()
        source = form.cleaned_data.get('source')
        if source:
            qs = qs.filter(source=source)
        date_from = form.cleaned_data.get('date_from')
        if date_from:
            qs = qs.filter(published_at__date__gte=date_from)
        date_to = form.cleaned_data.get('date_to')
        if date_to:
            qs = qs.filter(published_at__date__lte=date_to)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="rights_archive_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Title', 'URL', 'Source', 'Published', 'Tags', 'Summary'])
    for a in qs[:5000]:
        tag_str = ', '.join(t.name for t in a.tags.all())
        pub = a.published_at.strftime('%Y-%m-%d %H:%M') if a.published_at else ''
        writer.writerow([a.title, a.url, a.source.name if a.source else '', pub, tag_str, (a.summary or '')[:500]])
    return response


@staff_member_required
def add_by_url(request):
    """Manual add article by URL (scrape or paste metadata)."""
    form = AddByUrlForm(request.POST or None)
    if form.is_valid():
        from .utils import add_article_by_url
        url = form.cleaned_data['url']
        title = form.cleaned_data.get('title') or None
        summary = form.cleaned_data.get('summary') or None
        article, created = add_article_by_url(url, request.user, title=title, summary=summary)
        if created:
            messages.success(request, f'Added: {article.title}')
        else:
            messages.info(request, f'Article already exists: {article.title}')
        return redirect(article.get_absolute_url())
    return render(request, 'human_rights_archive/add_by_url.html', {'form': form})
