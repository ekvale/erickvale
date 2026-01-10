"""
Management command to add mango market simulation to featured apps.
"""
from django.core.management.base import BaseCommand
from erickvale.models import FeaturedApp
from datetime import datetime


class Command(BaseCommand):
    help = 'Adds mango market simulation to featured apps on homepage'

    def handle(self, *args, **options):
        app, created = FeaturedApp.objects.update_or_create(
            slug='mango-market-simulation',
            defaults={
                'name': 'Tanzania Mango Market Simulation',
                'description': 'An interactive simulation analyzing market forces between selling fresh mangoes versus processing them into dried mangoes. Explore price trends, profitability analysis, and strategic recommendations for Tanzanian farmers.',
                'icon': '🥭',
                'url': '/apps/mango-market/',
                'features': [
                    'Interactive market simulation with customizable parameters',
                    'Price trend analysis for fresh vs dried mangoes',
                    'Profitability comparison with detailed cost breakdowns',
                    'Strategic recommendations based on market conditions',
                    'Visual charts showing price volatility and revenue projections'
                ],
                'month': datetime.now().strftime('%B %Y'),
                'is_current_month': True,
                'is_published': True,
                'order': 0,
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{"Created" if created else "Updated"} Tanzania Mango Market Simulation'
            )
        )
