# Activity Media App - Deployment Guide

This guide covers deploying the new Activity Media app to your production server.

## What's New

The Activity Media app allows logged-in users with permission to:
- Upload photos and videos
- Tag activities
- Add location data (latitude/longitude)
- Search by tags and location
- View all media on an interactive map

## Pre-Deployment Checklist

- [ ] Code is committed and pushed to GitHub
- [ ] Server has sufficient disk space for media uploads
- [ ] Database has been backed up
- [ ] You have SSH access to the server

## Deployment Steps

### 1. SSH into Your Server

```bash
ssh erickvale@143.110.236.17
# or
ssh erickvale@erickvale.com
```

### 2. Navigate to Project Directory

```bash
cd /home/erickvale/erickvale
```

### 3. Pull Latest Changes from GitHub

```bash
git pull origin main
```

### 4. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 5. Install/Update Dependencies

```bash
pip install -r requirements.txt
```

**Note:** The new app doesn't require any additional packages beyond what's already in requirements.txt.

### 6. Run Database Migrations

This will create the new `activity_media_mediaitem` and `activity_media_activitytag` tables:

```bash
python manage.py migrate activity_media
```

Or run all migrations:

```bash
python manage.py migrate
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

This will collect the CSS files from the activity_media app.

### 8. Set Up Media Directory Permissions

Ensure the media directory exists and has proper permissions:

```bash
# Create media directory if it doesn't exist
mkdir -p /home/erickvale/erickvale/media/activity_media

# Set proper permissions
sudo chown -R erickvale:erickvale /home/erickvale/erickvale/media
chmod -R 755 /home/erickvale/erickvale/media
```

### 9. Create Activity Tags (Optional)

You can create activity tags via Django admin or using the shell:

```bash
python manage.py shell
```

In the shell:
```python
from activity_media.models import ActivityTag

# Create some example tags
ActivityTag.objects.get_or_create(name='Hiking')
ActivityTag.objects.get_or_create(name='Cooking')
ActivityTag.objects.get_or_create(name='Travel')
ActivityTag.objects.get_or_create(name='Sports')
ActivityTag.objects.get_or_create(name='Art')
ActivityTag.objects.get_or_create(name='Music')
ActivityTag.objects.get_or_create(name='Nature')
ActivityTag.objects.get_or_create(name='Food')

exit()
```

### 10. Grant Upload Permissions

Users need the `can_upload_media` permission to upload. Grant it via Django admin:

1. Go to `/admin/auth/user/` or `/admin/auth/group/`
2. Edit a user or group
3. Under "User permissions" or "Group permissions", find "Activity media | Media item | Can upload media"
4. Add the permission and save

Or via shell:

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from activity_media.models import MediaItem

# Get the permission
content_type = ContentType.objects.get_for_model(MediaItem)
permission = Permission.objects.get(
    codename='can_upload_media',
    content_type=content_type
)

# Grant to a specific user
user = User.objects.get(username='your_username')
user.user_permissions.add(permission)

# Or grant to all staff users
for user in User.objects.filter(is_staff=True):
    user.user_permissions.add(permission)

exit()
```

### 11. Restart the Application

```bash
sudo systemctl restart erickvale
```

### 12. Verify Deployment

Check the service status:

```bash
sudo systemctl status erickvale
```

View logs if needed:

```bash
sudo journalctl -u erickvale -f
```

### 13. Test the App

Visit these URLs to verify everything works:

- **Browse Media**: `https://erickvale.com/apps/activity-media/`
- **Map View**: `https://erickvale.com/apps/activity-media/map/`
- **Upload** (requires login + permission): `https://erickvale.com/apps/activity-media/upload/`
- **Admin**: `https://erickvale.com/admin/activity_media/`

## Nginx Configuration

The existing nginx configuration should already handle the new app routes. However, verify that media files are being served correctly:

Check `/etc/nginx/sites-available/erickvale` includes:

```nginx
location /media/ {
    alias /home/erickvale/erickvale/media/;
}
```

If not present, add it and reload nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Storage Considerations

### Disk Space

Media uploads can consume significant disk space. Monitor usage:

```bash
# Check disk usage
df -h

# Check media directory size
du -sh /home/erickvale/erickvale/media/
```

### File Size Limits

The app allows files up to 100MB. If you need to adjust this, edit:
- `activity_media/forms.py` - `clean_file()` method
- Nginx `client_max_body_size` setting (if needed)

To increase nginx upload limit:

```bash
sudo nano /etc/nginx/nginx.conf
```

Add or update:
```nginx
http {
    client_max_body_size 100M;
    ...
}
```

Then restart nginx:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

## Troubleshooting

### Media Files Not Uploading

1. Check directory permissions:
   ```bash
   ls -la /home/erickvale/erickvale/media/
   sudo chown -R erickvale:erickvale /home/erickvale/erickvale/media
   ```

2. Check nginx can serve media files:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. Check Django logs:
   ```bash
   sudo journalctl -u erickvale -f
   ```

### Map Not Loading

1. Check browser console for JavaScript errors
2. Verify Leaflet.js is loading (check network tab)
3. Ensure media items have valid latitude/longitude values

### Permission Denied Errors

1. Verify user has `can_upload_media` permission:
   ```bash
   python manage.py shell
   ```
   ```python
   from django.contrib.auth.models import User
   user = User.objects.get(username='your_username')
   print(user.has_perm('activity_media.can_upload_media'))
   ```

2. Grant permission if needed (see Step 10 above)

### Database Migration Errors

If migrations fail:

```bash
# Check migration status
python manage.py showmigrations activity_media

# If needed, fake the migration (use with caution)
python manage.py migrate activity_media --fake
```

## Maintenance

### Regular Backups

Include media files in your backup strategy:

```bash
# Backup database
sudo -u postgres pg_dump erickvale > /home/erickvale/backups/db_backup_$(date +%Y%m%d).sql

# Backup media files
tar -czf /home/erickvale/backups/media_backup_$(date +%Y%m%d).tar.gz /home/erickvale/erickvale/media/
```

### Clean Up Old Media

To remove media items older than X days:

```bash
python manage.py shell
```

```python
from activity_media.models import MediaItem
from datetime import timedelta
from django.utils import timezone

# Delete items older than 1 year
cutoff_date = timezone.now() - timedelta(days=365)
old_items = MediaItem.objects.filter(created_at__lt=cutoff_date)
count = old_items.count()
old_items.delete()
print(f"Deleted {count} old media items")
```

## Quick Update Script

Add this to your update script (`/home/erickvale/update_erickvale.sh`):

```bash
#!/bin/bash
cd /home/erickvale/erickvale
source venv/bin/activate
git pull origin main
pip install -r requirements.txt --quiet
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart erickvale
echo "Update complete! Check status with: sudo systemctl status erickvale"
```

## Support

If you encounter issues:

1. Check application logs: `sudo journalctl -u erickvale -f`
2. Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Check Django logs: `tail -f /home/erickvale/logs/django.log` (if configured)
4. Verify database connection: `python manage.py dbshell`

## Next Steps

After deployment:

1. Create activity tags via admin or shell
2. Grant upload permissions to users/groups
3. Test uploading a photo/video
4. Test adding location data
5. Verify map view displays uploaded media
6. Test search and filter functionality
