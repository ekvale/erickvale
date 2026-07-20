from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """The public, crawlable marketing pages of erickvale.com.

    Deliberately excludes anything behind login (projects/, contacts/,
    mdh/) and internal demo/admin tooling, since those aren't meant to rank.
    """
    protocol = 'https'

    changefreq_map = {
        'homepage': 'weekly',
        'about': 'monthly',
        'services': 'monthly',
        'contact': 'yearly',
        'math_bastion:play': 'monthly',
        'htac_public_about': 'monthly',
    }
    priority_map = {
        'homepage': 1.0,
        'about': 0.8,
        'math_bastion:play': 0.7,
        'htac_public_about': 0.6,
        'services': 0.6,
        'contact': 0.5,
    }

    def items(self):
        return list(self.changefreq_map.keys())

    def location(self, item):
        return reverse(item)

    def changefreq(self, item):
        return self.changefreq_map.get(item, 'monthly')

    def priority(self, item):
        return self.priority_map.get(item, 0.5)
