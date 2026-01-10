# Deploying the Mango Market Simulation App

This guide will help you deploy the new Tanzania Mango Market Simulation app to your live server.

## Quick Deployment Steps

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

**Note:** The mango_market app uses only standard Django and built-in Python libraries (no new dependencies were added).

### 6. Run database migrations

This will create the MarketSimulation model in your database:

```bash
python manage.py migrate mango_market
```

Or run all migrations:

```bash
python manage.py migrate
```

### 7. Set up the featured app entry (Optional)

To add the mango market simulation to your homepage as a featured app, run:

```bash
python manage.py setup_featured_app
```

This will create/update the FeaturedApp entry so it appears on your homepage.

### 8. Collect static files

```bash
python manage.py collectstatic --noinput
```

### 9. Restart the application server

```bash
sudo systemctl restart erickvale
```

Check status:

```bash
sudo systemctl status erickvale
```

View logs if needed:

```bash
sudo journalctl -u erickvale -f
```

### 10. Reload nginx (if needed)

Usually not necessary, but if you changed URL routing:

```bash
sudo nginx -t  # Test configuration first
sudo systemctl reload nginx
```

## Complete One-Line Update Script

You can run all these steps at once:

```bash
cd /home/erickvale/erickvale && source /home/erickvale/venv/bin/activate && git pull origin main && pip install -r requirements.txt && python manage.py migrate && python manage.py setup_featured_app && python manage.py collectstatic --noinput && sudo systemctl restart erickvale && echo "✅ Mango Market app deployed successfully!"
```

## Verification

After deployment, verify the app is working:

1. **Visit the app directly:**
   ```
   https://erickvale.com/apps/mango-market/
   ```

2. **Check the homepage:**
   ```
   https://erickvale.com/
   ```
   The mango market simulation should appear as a featured app if you ran `setup_featured_app`.

3. **Test the simulation:**
   - Try adjusting the quantity (kg) and simulation period (days)
   - Verify charts are displaying correctly
   - Check that cost breakdowns show proper calculations

## Troubleshooting

### If migrations fail:

```bash
python manage.py migrate mango_market --fake-initial
```

### If the app doesn't appear on homepage:

Make sure you ran:
```bash
python manage.py setup_featured_app
```

Then check in Django admin (`/admin/erickvale/featuredapp/`) that the app is marked as:
- `is_published = True`
- `is_current_month = True` (if you want it featured)

### If charts don't load:

Check browser console for errors. Make sure:
- Chart.js CDN is accessible (used from cdn.jsdelivr.net)
- Static files were collected properly
- No JavaScript errors in browser console

### Check application logs:

```bash
# Systemd logs
sudo journalctl -u erickvale -f

# Or check specific errors
sudo journalctl -u erickvale -n 50
```

### Check nginx logs:

```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## What Was Deployed

The mango_market app includes:

- **Models**: `MarketSimulation` - stores simulation results
- **Views**: Main simulation view and API endpoint
- **Templates**: Interactive HTML with Chart.js visualizations
- **Utils**: Market simulation logic with realistic Tanzanian market data
- **Admin**: Admin interface for viewing simulations
- **Management Command**: `setup_featured_app` to add to homepage

## Files Changed

- Added: `mango_market/` directory (entire new app)
- Modified: `erickvale/settings.py` (added 'mango_market' to INSTALLED_APPS)
- Modified: `erickvale/urls.py` (added URL routing for `/apps/mango-market/`)

## Notes

- The simulation uses mock data with realistic Tanzanian Shilling (TZS) pricing
- All calculations happen server-side for accuracy
- Charts are rendered client-side using Chart.js
- No additional Python packages were required (uses numpy/scipy already in requirements.txt)
