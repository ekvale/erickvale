from django.shortcuts import render


from datetime import datetime

def homepage(request):
    """Homepage view showcasing monthly apps."""
    current_date = datetime.now()
    current_month = current_date.strftime('%B %Y')
    
    apps = [
        {
            'name': 'Card Maker',
            'slug': 'cards',
            'description': 'Create custom cards based on your favorite subjects, novels, and games. Starting with Dungeon Crawler Carl characters, build your own card collection with stats, images, and descriptions.',
            'icon': '🃏',
            'url': '/apps/cards/',
            'features': [
                'Custom card creation',
                'DCC stat system (STR, INT, CON, DEX, CHR)',
                'Card sets and collections',
                'Character cards from favorite books'
            ],
            'month': 'January 2025',
            'status': 'active',
            'is_current_month': True
        },
        {
            'name': 'Emergency Preparedness',
            'slug': 'emergency',
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
            'status': 'active',
            'is_current_month': False
        },
        {
            'name': 'Blog',
            'slug': 'blog',
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
            'status': 'active',
            'is_current_month': False
        },
        # Future apps can be added here
    ]
    
    context = {
        'apps': apps,
        'current_month': current_month
    }
    
    return render(request, 'erickvale/homepage.html', context)

