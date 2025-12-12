from django.core.management.base import BaseCommand
from erickvale.models import FeaturedApp


class Command(BaseCommand):
    help = 'Populate initial featured apps data'

    def handle(self, *args, **options):
        # Create or update Qualitative Analysis for Literature (current month)
        literary_app, created = FeaturedApp.objects.update_or_create(
            slug='literary-analysis',
            defaults={
                'name': 'Qualitative Analysis for Literature',
                'description': 'A comprehensive qualitative analysis framework for literary texts. Upload works, apply systematic coding methodologies, and generate publication-quality reports with statistical analysis, visualizations, and thematic exploration. Currently featuring a complete analysis of Samuel R. Delany\'s Dhalgren.',
                'icon': '📚',
                'url': '/apps/literary/',
                'cover_image': None,
                'features': [
                    'Systematic qualitative coding',
                    'Comprehensive report generation (17 sections)',
                    'Statistical analysis (chi-square tests)',
                    'Thematic analysis and visualization',
                    'Word cloud and lexical analysis',
                    'Co-occurrence networks',
                    'Pre-built codebook templates'
                ],
                'month': 'December 2025',
                'is_current_month': True,
                'is_published': True,
                'order': 1,
            }
        )
        self.stdout.write(
            self.style.SUCCESS(f'{"Created" if created else "Updated"} Qualitative Analysis for Literature')
        )

        # Create or update The Power of Cards
        cards_app, created = FeaturedApp.objects.update_or_create(
            slug='cards',
            defaults={
                'name': 'The Power of Cards',
                'description': 'Cards transfix both youth and adults alike. Even money is a card with flavor text and mythological images not far removed from fantasy games. From baseball cards to tarot, to Brian Eno\'s Oblique Strategies, they have a way of grabbing attention and anchoring knowledge in playful and often unexpected ways.',
                'icon': '🃏',
                'url': '/apps/cards/',
                'cover_image': 'erickvale/images/king_and_death.avif',
                'features': [
                    'Custom card creation',
                    'DCC stat system (STR, INT, CON, DEX, CHR)',
                    'Card sets and collections',
                    'Character cards from favorite books'
                ],
                'month': 'January 2025',
                'is_current_month': False,
                'is_published': True,
                'order': 2,
            }
        )
        self.stdout.write(
            self.style.SUCCESS(f'{"Created" if created else "Updated"} The Power of Cards')
        )

        # Create or update Emergency Preparedness (unpublished)
        emergency_app, created = FeaturedApp.objects.update_or_create(
            slug='emergency',
            defaults={
                'name': 'Emergency Preparedness',
                'description': 'Spatial risk analysis and Point of Distribution (POD) location optimization for emergency planning in Minnesota. This month\'s featured application explores advanced geospatial analytics for disaster preparedness.',
                'icon': '🚨',
                'url': '/apps/emergency/',
                'features': [
                    'Interactive Leaflet.js mapping',
                    'POD optimization algorithm',
                    'Scenario-based risk analysis',
                    'Demographic data integration'
                ],
                'month': 'December 2024',
                'is_current_month': False,
                'is_published': False,  # Unpublished as requested
                'order': 3,
            }
        )
        self.stdout.write(
            self.style.SUCCESS(f'{"Created" if created else "Updated"} Emergency Preparedness (unpublished)')
        )

        # Create or update Blog
        blog_app, created = FeaturedApp.objects.update_or_create(
            slug='blog',
            defaults={
                'name': 'Blog',
                'description': 'Read about our monthly applications, development insights, upcoming projects, and technical deep-dives. The blog chronicles the journey of building each app and shares knowledge along the way.',
                'icon': '📝',
                'url': '/apps/blog/',
                'features': [
                    'Monthly app coverage',
                    'Development insights',
                    'Technical articles',
                    'Upcoming app previews'
                ],
                'month': 'Ongoing',
                'is_current_month': False,
                'is_published': True,
                'order': 4,
            }
        )
        self.stdout.write(
            self.style.SUCCESS(f'{"Created" if created else "Updated"} Blog')
        )

        self.stdout.write(
            self.style.SUCCESS('Successfully populated featured apps!')
        )

