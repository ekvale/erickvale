"""Utilities for Human Rights Archive (fetch, scrape, dedupe)."""
import hashlib
import logging
from datetime import datetime
from urllib.parse import urlparse

from django.utils import timezone

logger = logging.getLogger(__name__)


def add_article_by_url(url, user=None, title=None, summary=None, source=None):
    """
    Add or get an article by URL. Optionally scrape title/summary if not provided.
    Returns (article, created).
    """
    from .models import Article, Source

    existing = Article.objects.filter(url=url).first()
    if existing:
        return existing, False

    if not title or not summary:
        try:
            import requests
            from bs4 import BeautifulSoup
            headers = {'User-Agent': 'RightsArchive/1.0 (research; +https://example.com)'}
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            if not title:
                t = soup.find('title')
                title = (t.get_text().strip() if t else None) or url
            if not summary:
                meta = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
                summary = meta.get('content', '').strip() if meta and meta.get('content') else ''
        except Exception as e:
            logger.warning('Scrape failed for %s: %s', url, e)
            title = title or url
            summary = summary or ''

    article = Article.objects.create(
        title=(title or url)[:500],
        url=url,
        summary=(summary or '')[:5000],
        content='',
        published_at=timezone.now(),
        source=source,
        created_by=user,
    )
    return article, True


def normalize_feed_entry(entry, source=None):
    """Normalize a feedparser entry into (title, url, summary, content, published_at)."""
    title = (entry.get('title') or '').strip() or 'Untitled'
    link = entry.get('link') or ''
    if not link and entry.get('links'):
        for lnk in entry.get('links', []):
            href = lnk.get('href') if isinstance(lnk, dict) else getattr(lnk, 'href', None)
            rel = lnk.get('rel') if isinstance(lnk, dict) else getattr(lnk, 'rel', None)
            if href and str(href).startswith(('http://', 'https://')):
                if rel == 'alternate' or not link:
                    link = href
                if rel == 'alternate':
                    break
        if not link and entry.get('links'):
            first = entry['links'][0]
            link = first.get('href') if isinstance(first, dict) else getattr(first, 'href', '') or ''
    if not link:
        raw_id = (entry.get('id') or '').strip()
        if raw_id.startswith(('http://', 'https://')):
            link = raw_id
    if not link:
        return None
    summary = (entry.get('summary') or '').strip()[:5000]
    content = (entry.get('content', [{}])[0].get('value', '') if entry.get('content') else '')[:10000] or summary
    pub = None
    for key in ('published_parsed', 'updated_parsed'):
        p = entry.get(key)
        if p:
            try:
                from time import struct_time
                if isinstance(p, struct_time):
                    pub = timezone.make_aware(datetime(*p[:6]))
            except Exception:
                pass
            if pub:
                break
    return {
        'title': title[:500],
        'url': link,
        'summary': summary,
        'content': content,
        'published_at': pub,
        'source': source,
    }


def dedupe_key(url, published_at, title):
    """Stable key for deduplication."""
    raw = f"{url}|{published_at}|{hashlib.md5((title or '').encode()).hexdigest()}"
    return hashlib.sha256(raw.encode()).hexdigest()
