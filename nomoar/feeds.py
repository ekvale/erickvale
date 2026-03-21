"""RSS (and optional Atom) feeds for archive updates."""
from django.contrib.syndication.views import Feed
from django.urls import reverse

from .models import HistoricalEvent


class LatestEventsFeed(Feed):
    title = 'NOMOAR — Archive updates'
    description = 'Recently updated entries from the NOMOAR educational archive.'
    language = 'en'

    def link(self):
        return reverse('nomoar:timeline')

    def items(self):
        return HistoricalEvent.objects.order_by('-updated_at')[:50]

    def item_title(self, item):
        return f'{item.year}: {item.title}'

    def item_description(self, item):
        return item.summary[:800]

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.updated_at
