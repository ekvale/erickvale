from django.shortcuts import render
from datetime import datetime
from .models import FeaturedApp


def homepage(request):
    """Homepage view showcasing monthly apps."""
    current_date = datetime.now()
    current_month = current_date.strftime('%B %Y')
    
    # Get all published apps for sidebar
    published_apps = FeaturedApp.objects.filter(is_published=True)
    
    # Convert to dict format for template compatibility
    apps = []
    for app in published_apps:
        apps.append({
            'name': app.name,
            'slug': app.slug,
            'description': app.description,
            'icon': app.icon,
            'url': app.url,
            'cover_image': app.cover_image if app.cover_image else None,
            'features': app.features if app.features else [],
            'month': app.month,
            'status': 'active',
            'is_current_month': app.is_current_month,
        })
    
    # Create Media Gallery as the featured app
    media_gallery_app = {
        'name': 'Media Gallery',
        'slug': 'media-gallery',
        'description': 'Share your photos and videos from activities, tag them, and discover similar activities nearby. Upload media with automatic location detection and explore activities on an interactive map.',
        'icon': '📸',
        'url': '/apps/activity-media/',
        'cover_image': None,
        'features': [
            'Upload photos and videos with automatic type detection',
            'Tag activities and search by tags',
            'Automatic location extraction from photo metadata',
            'Interactive map to discover activities nearby',
            'Search within a radius from any location on the map'
        ],
        'month': current_month,
        'status': 'active',
        'is_current_month': True,
    }
    
    context = {
        'apps': apps,
        'current_month': current_month,
        'featured_app': media_gallery_app,
    }
    
    return render(request, 'erickvale/homepage.html', context)


def about(request):
    """About page view."""
    return render(request, 'erickvale/about.html')

