# Activity Media App - Quick Deployment Guide

## ✅ Pre-Deployment Status

- ✅ Code is committed and pushed to GitHub
- ✅ App is added to `INSTALLED_APPS` in `settings.py`
- ✅ URLs are configured at `/apps/activity-media/`
- ✅ Migrations are created and ready to run

## 🚀 Quick Deployment Steps

### 1. Connect to Your Server

```bash
ssh erickvale@143.110.236.17
# or
ssh erickvale@erickvale.com
```

### 2. Navigate to Project and Pull Latest Code

```bash
cd /home/erickvale/erickvale
git pull origin main
```

### 3. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 4. Install Dependencies (if needed)

```bash
pip install -r requirements.txt
```

**Note:** No new packages are required - the app uses existing dependencies (Django, Pillow for images).

### 5. Run Database Migrations

This creates the new tables for `activity_media_mediaitem` and `activity_media_activitytag`:

```bash
python manage.py migrate activity_media
```

Or run all pending migrations:

```bash
python manage.py migrate
```

### 6. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 7. Set Up Media Directory Permissions

```bash
# Create media subdirectory if needed
mkdir -p /home/erickvale/erickvale/media/activity_media

# Ensure proper permissions
sudo chown -R erickvale:erickvale /home/erickvale/erickvale/media
chmod -R 755 /home/erickvale/erickvale/media
```

### 8. Restart the Application

```bash
sudo systemctl restart erickvale
```

### 9. Verify Service is Running

```bash
sudo systemctl status erickvale
```

### 10. Grant Upload Permissions to Users

Users need the `can_upload_media` permission to upload. You can do this via:

**Option A: Django Admin**
1. Go to `https://erickvale.com/admin/auth/user/`
2. Select a user
3. Under "User permissions", find "Activity media | Media item | Can upload media"
4. Add the permission and save

**Option B: Django Shell**
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

### 11. Create Activity Tags (Optional)

You can create tags via admin or shell:

```bash
python manage.py shell
```

```python
from activity_media.models import ActivityTag

# Create example tags
ActivityTag.objects.get_or_create(name='Hiking')
ActivityTag.objects.get_or_create(name='Cooking')
ActivityTag.objects.get_or_create(name='Travel')
ActivityTag.objects.get_or_create(name='Sports')
ActivityTag.objects.get_or_create(name='Art')
ActivityTag.objects.get_or_create(name='Music')
ActivityTag.objects.get_or_create(name='Nature')
ActivityTag.objects.get_or_create(name='Food')
ActivityTag.objects.get_or_create(name='Photography')

exit()
```

## 🧪 Test the Deployment

Visit these URLs to verify everything works:

- **Browse Media**: `https://erickvale.com/apps/activity-media/`
- **Map View**: `https://erickvale.com/apps/activity-media/map/`
- **Upload** (requires login + permission): `https://erickvale.com/apps/activity-media/upload/`
- **Admin**: `https://erickvale.com/admin/activity_media/`

## 📋 Nginx Configuration Check

Verify that your nginx config includes media file serving. Check `/etc/nginx/sites-available/erickvale`:

```nginx
location /media/ {
    alias /home/erickvale/erickvale/media/;
}
```

If not present, add it and reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## ⚠️ Important Notes

### File Upload Size Limits

The app allows files up to **100MB**. If you need to increase this:

1. **Django**: Edit `activity_media/forms.py` - `clean_file()` method
2. **Nginx**: Update `/etc/nginx/nginx.conf`:
   ```nginx
   http {
       client_max_body_size 100M;
   }
   ```
   Then: `sudo nginx -t && sudo systemctl restart nginx`

### Disk Space Monitoring

Media uploads can consume significant disk space. Monitor usage:

```bash
# Check disk usage
df -h

# Check media directory size
du -sh /home/erickvale/erickvale/media/
```

## 🔍 Troubleshooting

### Media Files Not Uploading

1. Check permissions:
   ```bash
   ls -la /home/erickvale/erickvale/media/
   sudo chown -R erickvale:erickvale /home/erickvale/erickvale/media
   ```

2. Check logs:
   ```bash
   sudo journalctl -u erickvale -f
   ```

### Map Not Loading

- Check browser console for JavaScript errors
- Verify Leaflet.js CDN is accessible
- Ensure media items have valid latitude/longitude

### Permission Denied

Verify user has permission:
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
user = User.objects.get(username='your_username')
print(user.has_perm('activity_media.can_upload_media'))
```

## 📦 One-Line Update Script

For future updates, you can use this script:

```bash
cd /home/erickvale/erickvale && source venv/bin/activate && git pull origin main && pip install -r requirements.txt --quiet && python manage.py migrate && python manage.py collectstatic --noinput && sudo systemctl restart erickvale && echo "✅ Update complete!"
```

## 📚 Full Documentation

For detailed deployment instructions, see:
- `deploy/ACTIVITY_MEDIA_DEPLOYMENT.md` - Complete deployment guide
- `deploy/QUICK_DEPLOY.md` - General deployment guide

## ✅ Deployment Checklist

- [ ] Code pulled from GitHub
- [ ] Migrations run successfully
- [ ] Static files collected
- [ ] Media directory permissions set
- [ ] Application restarted
- [ ] Upload permissions granted to users
- [ ] Activity tags created (optional)
- [ ] Tested upload functionality
- [ ] Tested map view
- [ ] Verified media files are served correctly

---

**That's it!** Your Activity Media app should now be live and ready to use! 🎉
