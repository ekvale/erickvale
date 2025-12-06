from django.shortcuts import render
from datetime import datetime
from .models import FeaturedApp


def homepage(request):
    """Homepage view showcasing monthly apps."""
    current_date = datetime.now()
    current_month = current_date.strftime('%B %Y')
    
    # Get all published apps
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
    
    context = {
        'apps': apps,
        'current_month': current_month
    }
    
    return render(request, 'erickvale/homepage.html', context)


def about(request):
    """About page view."""
    return render(request, 'erickvale/about.html')

