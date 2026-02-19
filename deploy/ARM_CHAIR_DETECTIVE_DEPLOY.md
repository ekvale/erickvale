# Arm Chair Detective – Deploy to Live Server

Use this after pushing Arm Chair Detective to GitHub to make it live on your server.

## Prerequisites

- Server already running the erickvale Django project (see `FRAUD_DETECTION_QUICK_DEPLOY.md` or similar).
- No new Python packages were added for Arm Chair Detective.

---

## Steps to Make Arm Chair Detective Live

### 1. SSH into the server

```bash
ssh erickvale@143.110.236.17
# or
ssh erickvale@erickvale.com
```

### 2. Go to the project directory

```bash
cd /home/erickvale/erickvale
```

### 3. Pull the latest code from GitHub

```bash
git pull origin main
```

### 4. Activate the virtual environment

```bash
source /home/erickvale/venv/bin/activate
# or: source venv/bin/activate  (if venv is inside project)
```

### 5. Run database migrations

```bash
python manage.py migrate arm_chair_detective
```

### 5b. Backfill occupation (if you have existing suspects from before occupation was added)

```bash
python manage.py backfill_occupations
```

Or run all migrations:

```bash
python manage.py migrate
```

### 6. Generate suspect pool and create a sample case

```bash
# Generate suspects (100K = ~20 sec, 1M = ~4 min)
python manage.py generate_suspects --count 100000

# Create at least one playable case
python manage.py create_sample_case
```

### 7. (Optional) Add to featured apps on homepage

```bash
python manage.py populate_featured_apps
```

### 8. Collect static files

```bash
python manage.py collectstatic --noinput
```

### 9. Restart the application

```bash
sudo systemctl restart erickvale
```

Check that it’s running:

```bash
sudo systemctl status erickvale
```

---

## One-liner (after SSH)

```bash
cd /home/erickvale/erickvale && source /home/erickvale/venv/bin/activate && git pull origin main && python manage.py migrate && python manage.py generate_suspects --count 100000 && python manage.py create_sample_case && python manage.py collectstatic --noinput && sudo systemctl restart erickvale
```

*Note: First deploy will take longer due to suspect generation. For 1M suspects, run `generate_suspects --count 1000000` separately and wait ~4 minutes.*

---

## Verify

- **App:** `https://erickvale.com/apps/arm-chair-detective/`
- **Navbar:** "Arm Chair Detective" link is visible to everyone (no login required)
- Play a case: reveal clues, apply filters, narrow suspects, submit a guess

---

## Troubleshooting

**No cases showing:**
- Run `python manage.py create_sample_case`

**No suspects:**
- Run `python manage.py generate_suspects --count 100000`

**Check logs:**
```bash
sudo journalctl -u erickvale -f
tail -f /home/erickvale/logs/gunicorn_error.log
```
