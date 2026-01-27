"""
Management command to fetch RSS/Atom feeds for the Human Rights Archive.
Run periodically via cron, e.g.:
  0 */6 * * * cd /path/to/project && venv/bin/python manage.py fetch_rights_feeds
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from human_rights_archive.models import Source, Article, FeedFetchLog
from human_rights_archive.utils import normalize_feed_entry, suggest_article_tags

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch RSS/Atom feeds for the Human Rights Archive'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=int,
            metavar='PK',
            help='Fetch only this source (PK). Default: all active sources.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Ignore fetch_interval and fetch all active sources',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show per-entry details and feed bozo/status',
        )

    def handle(self, *args, **options):
        try:
            import feedparser
        except ImportError:
            self.stderr.write(self.style.ERROR('feedparser is required. pip install feedparser'))
            return

        qs = Source.objects.filter(is_active=True)
        if options.get('source'):
            qs = qs.filter(pk=options['source'])
        if not options.get('force'):
            from datetime import timedelta
            def should_skip(s):
                if s.last_fetched is None:
                    return False
                return s.last_fetched > (timezone.now() - timedelta(hours=s.fetch_interval_hours))
            qs = [s for s in qs if not should_skip(s)]
            if not qs:
                n_active = Source.objects.filter(is_active=True).count()
                if n_active == 0:
                    self.stdout.write(
                        self.style.WARNING(
                            'No RSS sources configured. Add feeds in Django admin '
                            '(Human Rights Archive → Sources) or run: python manage.py add_sample_rights_feed'
                        )
                    )
                else:
                    self.stdout.write('No sources due for fetch (use --force to fetch all).')
                return
        else:
            qs = list(qs)
        if not qs:
            self.stdout.write(self.style.WARNING('No active sources to fetch.'))
            return

        verbose = options.get('verbose', False)
        for source in qs:
            self._fetch_source(source, verbose=verbose)

    def _fetch_source(self, source, verbose=False):
        import feedparser

        log = FeedFetchLog.objects.create(source=source, status='running', message='')
        self.stdout.write(f'Fetching {source.name} ({source.url})...')
        try:
            parsed = feedparser.parse(
                source.url,
                agent='Mozilla/5.0 (compatible; RightsArchive/1.0; +https://example.com)',
            )
            entries = getattr(parsed, 'entries', []) or []
            if verbose:
                self.stdout.write(f'  Feed status: bozo={getattr(parsed, "bozo", False)} entries={len(entries)}')
                if getattr(parsed, 'bozo_exception', None):
                    self.stdout.write(self.style.WARNING(f'  Feed parse warning: {parsed.bozo_exception}'))
            added = 0
            skipped_no_link = 0
            skipped_duplicate = 0
            for entry in entries:
                data = normalize_feed_entry(entry, source=source)
                if not data:
                    skipped_no_link += 1
                    if verbose and entry.get('title'):
                        self.stdout.write(self.style.WARNING(f'  Skipped (no URL): {entry.get("title", "")[:50]}'))
                    continue
                url = data['url']
                if Article.objects.filter(url=url).exists():
                    skipped_duplicate += 1
                    continue
                article = Article.objects.create(
                    title=data['title'],
                    url=url,
                    summary=data['summary'],
                    content=data['content'],
                    published_at=data['published_at'],
                    source=source,
                )
                tags = suggest_article_tags(article.title, article.summary, article.content)
                if tags:
                    article.tags.add(*tags)
                added += 1
                if verbose:
                    self.stdout.write(f'  + {data["title"][:60]}')
            source.last_fetched = timezone.now()
            source.last_fetch_status = 'success'
            source.last_fetch_message = f'Added {added} (feed had {len(entries)} entries)'
            source.save(update_fields=['last_fetched', 'last_fetch_status', 'last_fetch_message'])
            log.completed_at = timezone.now()
            log.status = 'success'
            log.articles_added = added
            log.message = source.last_fetch_message
            log.save()
            msg = f'  {source.name}: added {added}'
            if added == 0 and entries:
                msg += f' (all {len(entries)} already in DB or skipped)'
            elif added == 0:
                msg += f' — feed had 0 entries. Check URL or try --verbose'
            self.stdout.write(self.style.SUCCESS(msg))
            if verbose and (skipped_no_link or skipped_duplicate):
                self.stdout.write(f'  Skipped: {skipped_no_link} no URL, {skipped_duplicate} duplicates')
        except Exception as e:
            source.last_fetched = timezone.now()
            source.last_fetch_status = 'error'
            source.last_fetch_message = str(e)[:500]
            source.save(update_fields=['last_fetched', 'last_fetch_status', 'last_fetch_message'])
            log.completed_at = timezone.now()
            log.status = 'error'
            log.message = source.last_fetch_message
            log.save()
            self.stderr.write(self.style.ERROR(f'  {source.name}: {e}'))
            logger.exception('Feed fetch failed: %s', source.url)
