# Human Rights Archive – Deploy to Live Server

This app is **staff-only**: the navbar link appears only when the user is logged in and has `is_staff=True`. The app lives at `/apps/human-rights-archive/`.

## 1. Push to GitHub (from your machine)

From the project root:

```powershell
cd d:\erickvale
git add human_rights_archive/ erickvale/settings.py erickvale/urls.py erickvale/templates/erickvale/homepage.html requirements.txt deploy/HUMAN_RIGHTS_ARCHIVE_DEPLOY.md
git status   # review
git commit -m "Add Human Rights & Constitutional Violations Archive (staff-only)"
git push origin main
```

(Use your real branch name if it’s not `main`.)

## 2. On the server: pull and install deps

SSH in and pull, then install any new Python packages:

```bash
cd /home/erickvale/erickvale   # or your app root
git pull origin main

source venv/bin/activate
pip install -r requirements.txt
```

New dependencies for this app: `feedparser`, `beautifulsoup4` (and `requests`, which you likely already have).

## 3. Run migrations

```bash
source venv/bin/activate
python manage.py migrate human_rights_archive
```

## 4. Load default tags (required for auto-tagging)

Tags include ICE/immigration-specific ones and keywords used to auto-tag articles:

```bash
python manage.py load_rights_tags
```

This creates/updates tags such as: ICE, CBP, DHS, immigration-detention, family-separation, deportation, asylum, border, plus human rights/constitutional tags. Each tag’s `keywords` field (comma-separated) is used to match article title/summary/content when ingesting.

- `--clear` — remove all tags first, then reload
- `--ice-only` — add only ICE/immigration-related tags

**Tag existing articles** (after loading tags and fetching articles):

```bash
python manage.py tag_existing_articles
```

Use `--dry-run` to see what would be tagged without saving.

## 5. Collect static files

If you use a separate static root:

```bash
python manage.py collectstatic --noinput
```

## 6. Restart the app

```bash
sudo systemctl restart erickvale
# or whatever your gunicorn/uwsgi service is named
```

## 7. Add feeds and schedule fetches

**If you have no articles yet:** add at least one working RSS source, then fetch:

```bash
python manage.py add_sample_rights_feed    # adds BBC World News
python manage.py fetch_rights_feeds --force
```

**To add many major news feeds at once** (BBC, NYT, Guardian, NPR, CNN, WaPo, Al Jazeera, CBS, NBC, PBS, Politico, ProPublica, LA Times, Vox, Axios, etc.):

```bash
python manage.py add_sample_rights_feed --major-news
python manage.py fetch_rights_feeds --force
```

Or in Django Admin: **Human Rights Archive → Sources** → add RSS/Atom feed URLs (name, URL, type). Some sites (e.g. Human Rights Watch) may return HTML instead of XML to scripts; use feeds that serve RSS/XML to generic clients (e.g. `https://feeds.bbci.co.uk/news/world/rss.xml`).

- To fetch articles from all active sources:

  ```bash
  python manage.py fetch_rights_feeds
  ```
- Use `--verbose` to see feed status and per-entry skips; use `--force` to ignore fetch_interval.

- To run this on a schedule (e.g. every 6 hours), add a cron job as the app user:

  ```bash
  crontab -u erickvale -e
  ```

  Example line (run every 6 hours):

  ```cron
  0 */6 * * * cd /home/erickvale/erickvale && /home/erickvale/erickvale/venv/bin/python manage.py fetch_rights_feeds
  ```

- Optional: fetch only one source by PK:  
  `python manage.py fetch_rights_feeds --source 1`  
  Or ignore “last fetched” and fetch all:  
  `python manage.py fetch_rights_feeds --force`

## 8. Who can see it

- **URL:** `https://yourdomain.com/apps/human-rights-archive/`
- **Navbar:** The “Rights Archive” link is shown only to users with `user.is_authenticated and user.is_staff`.
- **Views:** All archive views use `@staff_member_required`, so only staff can access them. Non-staff users get a redirect to the login (or 403, depending on your config).

## 9. Quick checks

- Log in as a staff user and open the homepage → “Rights Archive” should appear in the nav.
- Open `/apps/human-rights-archive/` → dashboard loads.
- In Admin, add a Source (e.g. an ACLU or HRW RSS URL), then run `fetch_rights_feeds` and confirm articles appear on the Articles list and dashboard.
