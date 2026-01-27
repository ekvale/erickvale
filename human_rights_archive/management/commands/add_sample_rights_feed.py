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

# Major news RSS feeds from major outlets. Use --major-news to add all.
# URLs are standard RSS/Atom endpoints; some sites may block or redirect bots.
MAJOR_NEWS_FEEDS = [
    # BBC
    {'name': 'BBC Top Stories', 'url': 'https://feeds.bbci.co.uk/news/rss.xml', 'source_type': 'rss'},
    {'name': 'BBC World', 'url': 'https://feeds.bbci.co.uk/news/world/rss.xml', 'source_type': 'rss'},
    {'name': 'BBC UK', 'url': 'https://feeds.bbci.co.uk/news/uk/rss.xml', 'source_type': 'rss'},
    {'name': 'BBC Business', 'url': 'https://feeds.bbci.co.uk/news/business/rss.xml', 'source_type': 'rss'},
    {'name': 'BBC Politics', 'url': 'https://feeds.bbci.co.uk/news/politics/rss.xml', 'source_type': 'rss'},
    {'name': 'BBC Technology', 'url': 'https://feeds.bbci.co.uk/news/technology/rss.xml', 'source_type': 'rss'},
    {'name': 'BBC Science & Environment', 'url': 'https://feeds.bbci.co.uk/news/science_and_environment/rss.xml', 'source_type': 'rss'},
    # New York Times
    {'name': 'NYT Home', 'url': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml', 'source_type': 'rss'},
    {'name': 'NYT World', 'url': 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml', 'source_type': 'rss'},
    {'name': 'NYT U.S.', 'url': 'https://rss.nytimes.com/services/xml/rss/nyt/US.xml', 'source_type': 'rss'},
    {'name': 'NYT Politics', 'url': 'https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml', 'source_type': 'rss'},
    {'name': 'NYT Business', 'url': 'https://rss.nytimes.com/services/xml/rss/nyt/Business.xml', 'source_type': 'rss'},
    {'name': 'NYT Technology', 'url': 'https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml', 'source_type': 'rss'},
    {'name': 'NYT Science', 'url': 'https://rss.nytimes.com/services/xml/rss/nyt/Science.xml', 'source_type': 'rss'},
    {'name': 'NYT Arts', 'url': 'https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml', 'source_type': 'rss'},
    # Guardian
    {'name': 'Guardian World', 'url': 'https://www.theguardian.com/world/rss', 'source_type': 'rss'},
    {'name': 'Guardian UK', 'url': 'https://www.theguardian.com/uk/rss', 'source_type': 'rss'},
    {'name': 'Guardian US', 'url': 'https://www.theguardian.com/us/rss', 'source_type': 'rss'},
    {'name': 'Guardian Politics', 'url': 'https://www.theguardian.com/politics/rss', 'source_type': 'rss'},
    {'name': 'Guardian Business', 'url': 'https://www.theguardian.com/business/rss', 'source_type': 'rss'},
    {'name': 'Guardian Technology', 'url': 'https://www.theguardian.com/technology/rss', 'source_type': 'rss'},
    {'name': 'Guardian Environment', 'url': 'https://www.theguardian.com/environment/rss', 'source_type': 'rss'},
    # NPR
    {'name': 'NPR Top Stories', 'url': 'https://feeds.npr.org/1002/rss.xml', 'source_type': 'rss'},
    {'name': 'NPR National', 'url': 'https://feeds.npr.org/1003/rss.xml', 'source_type': 'rss'},
    {'name': 'NPR World', 'url': 'https://feeds.npr.org/1004/rss.xml', 'source_type': 'rss'},
    {'name': 'NPR Politics', 'url': 'https://feeds.npr.org/1014/rss.xml', 'source_type': 'rss'},
    {'name': 'NPR Business', 'url': 'https://feeds.npr.org/1006/rss.xml', 'source_type': 'rss'},
    {'name': 'NPR Technology', 'url': 'https://feeds.npr.org/1019/rss.xml', 'source_type': 'rss'},
    {'name': 'NPR Science', 'url': 'https://feeds.npr.org/1007/rss.xml', 'source_type': 'rss'},
    # CNN
    {'name': 'CNN Top Stories', 'url': 'http://rss.cnn.com/rss/cnn_topstories.rss', 'source_type': 'rss'},
    {'name': 'CNN World', 'url': 'http://rss.cnn.com/rss/cnn_world.rss', 'source_type': 'rss'},
    {'name': 'CNN U.S.', 'url': 'http://rss.cnn.com/rss/cnn_us.rss', 'source_type': 'rss'},
    {'name': 'CNN Politics', 'url': 'http://rss.cnn.com/rss/cnn_allpolitics.rss', 'source_type': 'rss'},
    {'name': 'CNN Money', 'url': 'http://rss.cnn.com/rss/money_news_international.rss', 'source_type': 'rss'},
    # Al Jazeera
    {'name': 'Al Jazeera', 'url': 'https://www.aljazeera.com/xml/rss/all.xml', 'source_type': 'rss'},
    # Washington Post
    {'name': 'Washington Post Politics', 'url': 'https://feeds.washingtonpost.com/rss/politics', 'source_type': 'rss'},
    {'name': 'Washington Post National', 'url': 'https://feeds.washingtonpost.com/rss/national', 'source_type': 'rss'},
    {'name': 'Washington Post World', 'url': 'https://feeds.washingtonpost.com/rss/world', 'source_type': 'rss'},
    {'name': 'Washington Post Business', 'url': 'https://feeds.washingtonpost.com/rss/business', 'source_type': 'rss'},
    # Politico
    {'name': 'Politico', 'url': 'https://www.politico.com/rss/politics08.xml', 'source_type': 'rss'},
    # CBS News
    {'name': 'CBS News', 'url': 'https://www.cbsnews.com/latest/rss/main', 'source_type': 'rss'},
    # NBC News
    {'name': 'NBC News', 'url': 'https://feeds.nbcnews.com/nbcnews/public/news', 'source_type': 'rss'},
    # USA Today
    {'name': 'USA Today Top', 'url': 'https://rssfeeds.usatoday.com/UsatodaycomNation-TopStories', 'source_type': 'rss'},
    # PBS NewsHour
    {'name': 'PBS NewsHour Headlines', 'url': 'https://www.pbs.org/newshour/feeds/rss/headlines', 'source_type': 'rss'},
    {'name': 'PBS NewsHour Politics', 'url': 'https://www.pbs.org/newshour/feeds/rss/politics', 'source_type': 'rss'},
    {'name': 'PBS NewsHour World', 'url': 'https://www.pbs.org/newshour/feeds/rss/world', 'source_type': 'rss'},
    # ProPublica
    {'name': 'ProPublica', 'url': 'https://www.propublica.org/feeds/news', 'source_type': 'rss'},
    # LA Times
    {'name': 'LA Times', 'url': 'https://www.latimes.com/california/rss2.0.xml', 'source_type': 'rss'},
    # Vox
    {'name': 'Vox', 'url': 'https://www.vox.com/rss/index.xml', 'source_type': 'rss'},
    # Axios
    {'name': 'Axios', 'url': 'https://api.axios.com/feed/', 'source_type': 'rss'},
]


class Command(BaseCommand):
    help = 'Add sample RSS sources. Use --all for sample set, --major-news for many major outlets.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Add all sample feeds (default: add just the first one)',
        )
        parser.add_argument(
            '--major-news',
            action='store_true',
            help='Add many major news RSS feeds (BBC, NYT, Guardian, NPR, CNN, WaPo, etc.)',
        )

    def handle(self, *args, **options):
        if options.get('major_news'):
            to_add = MAJOR_NEWS_FEEDS
        elif options.get('all'):
            to_add = SAMPLE_FEEDS
        else:
            to_add = SAMPLE_FEEDS[:1]

        created_count = 0
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
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Added: {src.name}'))
            else:
                self.stdout.write(f'Already exists: {src.name}')

        self.stdout.write(self.style.SUCCESS(f'Done. Added {created_count} new source(s). Run: python manage.py fetch_rights_feeds --force'))
