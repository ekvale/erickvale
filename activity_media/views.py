from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import OperationalError, ProgrammingError
from django.db.utils import DatabaseError
from .models import MediaItem, ActivityTag
from .forms import MediaItemForm
import json
import logging

logger = logging.getLogger(__name__)


@login_required
@permission_required('activity_media.can_upload_media', raise_exception=True)
def upload_media(request):
    """View for uploading new media items."""
    if request.method == 'POST':
        form = MediaItemForm(request.POST, request.FILES)
        if form.is_valid():
            media_item = form.save(commit=False)
            media_item.user = request.user
            media_item.save()
            form.save_m2m()  # Save many-to-many relationships (activity_tags)
            messages.success(request, f'Your {media_item.media_type} has been uploaded successfully!')
            return redirect('activity_media:detail', pk=media_item.pk)
    else:
        form = MediaItemForm()
    
    return render(request, 'activity_media/upload.html', {'form': form})


def media_list(request):
    """List all media items with search and filter capabilities."""
    # Check if table exists, if not return empty queryset
    try:
        media_items = MediaItem.objects.filter(is_public=True).select_related('user').prefetch_related('activity_tags')
    except (OperationalError, ProgrammingError, DatabaseError) as e:
        # Table doesn't exist yet (migrations not run)
        # Log the error for debugging
        logger.error(f"Database error in media_list: {str(e)}", exc_info=True)
        # Return empty context with helpful message
        context = {
            'page_obj': None,
            'search_query': '',
            'tag_filter': '',
            'media_type_filter': '',
            'all_tags': [],
            'migration_error': True,
        }
        return render(request, 'activity_media/list.html', context)
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error in media_list: {str(e)}", exc_info=True)
        # Still try to render with empty context
        context = {
            'page_obj': None,
            'search_query': '',
            'tag_filter': '',
            'media_type_filter': '',
            'all_tags': [],
            'migration_error': True,
        }
        return render(request, 'activity_media/list.html', context)
    
    # Search by title/description
    search_query = request.GET.get('search', '')
    if search_query:
        media_items = media_items.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location_name__icontains=search_query)
        )
    
    # Filter by activity tag
    tag_filter = request.GET.get('tag', '')
    if tag_filter:
        media_items = media_items.filter(activity_tags__name__icontains=tag_filter)
    
    # Filter by media type
    media_type_filter = request.GET.get('type', '')
    if media_type_filter:
        media_items = media_items.filter(media_type=media_type_filter)
    
    # Filter by location (within radius)
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    radius = request.GET.get('radius', 10)  # Default 10km radius
    
    if lat and lon:
        try:
            # Filter by approximate bounding box (simple distance calculation)
            # 1 degree latitude ≈ 111 km, longitude varies by latitude
            lat_float = float(lat)
            lon_float = float(lon)
            radius_deg = float(radius) / 111.0  # Rough conversion: 1 degree ≈ 111 km
            
            media_items = media_items.filter(
                latitude__gte=lat_float - radius_deg,
                latitude__lte=lat_float + radius_deg,
                longitude__gte=lon_float - radius_deg,
                longitude__lte=lon_float + radius_deg,
            )
        except (ValueError, TypeError):
            pass
    
    # Pagination
    try:
        paginator = Paginator(media_items, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logger.error(f"Pagination error: {str(e)}", exc_info=True)
        # If pagination fails, return empty page
        from django.core.paginator import EmptyPage, PageNotAnInteger
        page_obj = None
    
    # Get all tags for filter dropdown
    try:
        all_tags = ActivityTag.objects.all().order_by('name')
    except (OperationalError, ProgrammingError):
        all_tags = []
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'tag_filter': tag_filter,
        'media_type_filter': media_type_filter,
        'all_tags': all_tags,
    }
    
    return render(request, 'activity_media/list.html', context)


def media_detail(request, pk):
    """View individual media item details."""
    media_item = get_object_or_404(MediaItem.objects.select_related('user').prefetch_related('activity_tags'), pk=pk)
    
    # Check if user has permission to view
    if not media_item.is_public and media_item.user != request.user:
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to view this media.')
            return redirect('activity_media:list')
        messages.error(request, 'You do not have permission to view this media.')
        return redirect('activity_media:list')
    
    return render(request, 'activity_media/detail.html', {'media_item': media_item})


def media_map(request):
    """Display all media items on a map."""
    media_items = MediaItem.objects.filter(
        is_public=True,
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('user').prefetch_related('activity_tags')
    
    # Filter by tag if provided
    tag_filter = request.GET.get('tag', '')
    if tag_filter:
        media_items = media_items.filter(activity_tags__name__icontains=tag_filter)
    
    # Filter by media type
    media_type_filter = request.GET.get('type', '')
    if media_type_filter:
        media_items = media_items.filter(media_type=media_type_filter)
    
    # Prepare data for map
    map_data = []
    for item in media_items:
        map_data.append({
            'id': item.pk,
            'title': item.title or item.file.name,
            'type': item.media_type,
            'lat': float(item.latitude),
            'lon': float(item.longitude),
            'location_name': item.location_name,
            'url': item.get_absolute_url(),
            'thumbnail': item.thumbnail.url if item.thumbnail else None,
            'tags': [tag.name for tag in item.activity_tags.all()],
        })
    
    # Get all tags for filter dropdown
    all_tags = ActivityTag.objects.all().order_by('name')
    
    context = {
        'map_data': json.dumps(map_data),
        'all_tags': all_tags,
        'tag_filter': tag_filter,
        'media_type_filter': media_type_filter,
    }
    
    return render(request, 'activity_media/map.html', context)


@require_http_methods(["GET"])
def media_api(request):
    """API endpoint for fetching media items as JSON (for AJAX requests)."""
    media_items = MediaItem.objects.filter(
        is_public=True,
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('user').prefetch_related('activity_tags')
    
    # Apply filters
    tag_filter = request.GET.get('tag', '')
    if tag_filter:
        media_items = media_items.filter(activity_tags__name__icontains=tag_filter)
    
    media_type_filter = request.GET.get('type', '')
    if media_type_filter:
        media_items = media_items.filter(media_type=media_type_filter)
    
    data = []
    for item in media_items:
        data.append({
            'id': item.pk,
            'title': item.title or item.file.name,
            'type': item.media_type,
            'lat': float(item.latitude),
            'lon': float(item.longitude),
            'location_name': item.location_name,
            'url': item.get_absolute_url(),
            'thumbnail': item.thumbnail.url if item.thumbnail else None,
            'tags': [tag.name for tag in item.activity_tags.all()],
        })
    
    return JsonResponse({'media_items': data})
