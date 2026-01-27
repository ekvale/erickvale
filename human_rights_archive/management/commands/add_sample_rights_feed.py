"""
Add a sample RSS source so you can test the archive. Run this, then run fetch_rights_feeds.
"""
from django.core.management.base import BaseCommand
from human_rights_archive.models import Source


# Known-good RSS feeds. First one is used by default (add_sample_rights_feed without --all).
# Some sites (e.g. HRW) may return HTML to scripts; use feeds that serve XML to generic clients.
SAMPLE_FEEDS = [
    {'name': 'BBC World News', 'url': 'https://feeds.bbci.co.uk/news/world/rss.xml', 'source_type': 'rss'},
    {'name': 'Human Rights Watch News', 'url': 'https://www.hrw.org/news/feed', 'source_type': 'rss'},
    {'name': 'ACLU of DC', 'url': 'https://www.acludc.org/en/rss.xml', 'source_type': 'rss'},
    {'name': 'Just Security (NYU)', 'url': 'https://www.justsecurity.org/feed/', 'source_type': 'rss'},
]


class Command(BaseCommand):
    help = 'Add one or more sample RSS sources for testing. Then run fetch_rights_feeds.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Add all sample feeds (default: add just the first one)',
        )

    def handle(self, *args, **options):
        to_add = SAMPLE_FEEDS if options.get('all') else SAMPLE_FEEDS[:1]
        for feed in to_add:
            src, created = Source.objects.get_or_create(
                url=feed['url'],
                defaults={
                    'name': feed['name'],
                    'source_type': feed.get('source_type', 'rss'),
                    'is_active': True,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Added: {src.name} ({src.url})'))
            else:
                self.stdout.write(f'Already exists: {src.name}')
        self.stdout.write(self.style.SUCCESS('Run: python manage.py fetch_rights_feeds --force'))
