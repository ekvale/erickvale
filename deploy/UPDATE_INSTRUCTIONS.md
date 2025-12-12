# Server Update Instructions

## Quick Update Process

Follow these steps to update your server with the latest changes from GitHub:

### 1. SSH into your server

```bash
ssh erickvale@your-server-ip
# or
ssh erickvale@erickvale.com
```

### 2. Navigate to the project directory

```bash
cd /home/erickvale/erickvale
```

### 3. Pull the latest changes from GitHub

```bash
git pull origin main
```

### 4. Activate your virtual environment

```bash
source /home/erickvale/venv/bin/activate
```

### 5. Install any new dependencies (if requirements.txt changed)

```bash
pip install -r requirements.txt
```

### 6. Run database migrations

```bash
python manage.py migrate
```

### 7. Collect static files (if static files changed)

```bash
python manage.py collectstatic --noinput
```

### 8. Load codes (if needed for Dhalgren analysis)

```bash
python manage.py load_dhalgren_codes
```

### 9. Restart the application server

**Using systemd service (recommended):**
```bash
sudo systemctl restart erickvale
# Check status
sudo systemctl status erickvale
# View logs
sudo journalctl -u erickvale -f
```

**If using gunicorn directly:**
```bash
# Find and kill the process
pkill -f gunicorn
# Restart (adjust path/command as needed)
cd ~/erickvale
source venv/bin/activate
gunicorn erickvale.wsgi:application --bind 127.0.0.1:8000 --workers 3 --daemon
```

**If using supervisor:**
```bash
sudo supervisorctl restart erickvale
```

### 10. Reload nginx (usually not needed, but if config changed)

```bash
sudo nginx -t  # Test configuration first
sudo systemctl reload nginx
```

## Complete Update Script

You can also create a simple update script for convenience:

```bash
#!/bin/bash
# save as /home/erickvale/update_erickvale.sh

cd /home/erickvale/erickvale
source /home/erickvale/venv/bin/activate
git pull origin main
pip install -r requirements.txt --quiet
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart erickvale
echo "Update complete! Check status with: sudo systemctl status erickvale"
```

Make it executable:
```bash
chmod +x ~/update_erickvale.sh
```

Then run updates with:
```bash
~/update_erickvale.sh
```

## Troubleshooting

### If migrations fail:
```bash
python manage.py migrate --fake-initial
```

### If static files don't update:
```bash
python manage.py collectstatic --noinput --clear
```

### Check application logs:
```bash
# Systemd logs
sudo journalctl -u erickvale -f

# Or if using gunicorn directly
tail -f /var/log/gunicorn/error.log
```

### Check nginx logs:
```bash
sudo tail -f /var/log/nginx/error.log
```

## Verification

After updating, verify the changes:

1. Visit your site: https://erickvale.com/apps/literary/
2. Check that the coding interface loads properly
3. Verify that codes are loaded (should see 104 codes for Dhalgren codebook)
4. Test creating/editing a memo to ensure rich text editor works

## Notes

- The update process is designed to be non-destructive
- Database migrations are backward-compatible when possible
- Always test in a staging environment first if available
- Keep backups of your database before major updates

