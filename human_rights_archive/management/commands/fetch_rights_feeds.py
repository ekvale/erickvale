"""
Management command to fetch RSS/Atom feeds for the Human Rights Archive.
Run periodically via cron, e.g.:
  0 */6 * * * cd /path/to/project && venv/bin/python manage.py fetch_rights_feeds
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from human_rights_archive.models import Source, Article, FeedFetchLog
from human_rights_archive.utils import normalize_feed_entry

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
                self.stdout.write('No sources due for fetch (use --force to fetch all).')
                return
        else:
            qs = list(qs)

        for source in qs:
            self._fetch_source(source)

    def _fetch_source(self, source):
        import feedparser

        log = FeedFetchLog.objects.create(source=source, status='running', message='')
        self.stdout.write(f'Fetching {source.name} ({source.url})...')
        try:
            # Respect rate limits: simple 1s pause would go here if needed
            parsed = feedparser.parse(
                source.url,
                agent='RightsArchive/1.0 (research; +https://example.com)',
            )
            added = 0
            for entry in getattr(parsed, 'entries', []) or []:
                data = normalize_feed_entry(entry, source=source)
                if not data:
                    continue
                url = data['url']
                if Article.objects.filter(url=url).exists():
                    continue
                Article.objects.create(
                    title=data['title'],
                    url=url,
                    summary=data['summary'],
                    content=data['content'],
                    published_at=data['published_at'],
                    source=source,
                )
                added += 1
            source.last_fetched = timezone.now()
            source.last_fetch_status = 'success'
            source.last_fetch_message = f'Added {added} articles'
            source.save(update_fields=['last_fetched', 'last_fetch_status', 'last_fetch_message'])
            log.completed_at = timezone.now()
            log.status = 'success'
            log.articles_added = added
            log.message = source.last_fetch_message
            log.save()
            self.stdout.write(self.style.SUCCESS(f'  {source.name}: added {added}'))
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
