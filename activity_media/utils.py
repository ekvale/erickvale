"""
Utility functions for activity_media app.
"""
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def get_exif_data(image):
    """Extract EXIF data from PIL Image."""
    exif_data = {}
    try:
        if hasattr(image, '_getexif'):
            exif = image._getexif()
            if exif is not None:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value
    except Exception as e:
        logger.warning(f"Error reading EXIF data: {e}")
    return exif_data


def get_gps_data(exif_data):
    """Extract GPS data from EXIF data."""
    gps_data = {}
    try:
        if 'GPSInfo' in exif_data:
            for key, value in exif_data['GPSInfo'].items():
                tag = GPSTAGS.get(key, key)
                gps_data[tag] = value
    except Exception as e:
        logger.warning(f"Error reading GPS data: {e}")
    return gps_data


def convert_to_degrees(value):
    """Convert GPS coordinates to decimal degrees."""
    try:
        d, m, s = value
        return float(d) + (float(m) / 60.0) + (float(s) / 3600.0)
    except (ValueError, TypeError):
        return None


def get_lat_lon_from_exif(image_path):
    """
    Extract latitude and longitude from image EXIF data.
    
    Returns:
        tuple: (latitude, longitude) as Decimal, or (None, None) if not found
    """
    try:
        with Image.open(image_path) as image:
            exif_data = get_exif_data(image)
            gps_data = get_gps_data(exif_data)
            
            if not gps_data:
                return None, None
            
            # Get GPS coordinates
            lat_ref = gps_data.get('GPSLatitudeRef', 'N')
            lon_ref = gps_data.get('GPSLongitudeRef', 'E')
            lat = gps_data.get('GPSLatitude')
            lon = gps_data.get('GPSLongitude')
            
            if lat and lon:
                # Convert to decimal degrees
                lat_decimal = convert_to_degrees(lat)
                lon_decimal = convert_to_degrees(lon)
                
                # Apply reference (N/S, E/W)
                if lat_ref == 'S':
                    lat_decimal = -lat_decimal
                if lon_ref == 'W':
                    lon_decimal = -lon_decimal
                
                # Round to 6 decimal places (about 0.1 meter precision)
                lat_decimal = round(lat_decimal, 6)
                lon_decimal = round(lon_decimal, 6)
                
                return Decimal(str(lat_decimal)), Decimal(str(lon_decimal))
            
    except Exception as e:
        logger.warning(f"Error extracting GPS from image {image_path}: {e}")
    
    return None, None


def extract_location_from_file(file_path, media_type):
    """
    Extract location from photo or video file.
    
    Args:
        file_path: Path to the uploaded file
        media_type: 'photo' or 'video'
    
    Returns:
        tuple: (latitude, longitude) as Decimal, or (None, None) if not found
    """
    if media_type == 'photo':
        return get_lat_lon_from_exif(file_path)
    elif media_type == 'video':
        # Video GPS extraction is more complex and requires additional libraries
        # For now, return None - can be enhanced later with exifread or hachoir
        # Most video formats don't store GPS data in a standard way
        return None, None
    
    return None, None
