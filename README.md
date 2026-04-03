# eric kvale

A monthly collection of applications built with Django.

## Project Structure

```
erickvale/
├── erickvale/          # Main project configuration
├── blog/               # Blog app for writing about monthly apps
├── emergency_preparedness/  # Emergency Preparedness app (December 2025)
│   ├── demographic_data.json  # Demographic data for Minnesota cities
│   └── ...
├── docs/               # Documentation files
├── staticfiles/        # Collected static files (generated)
├── manage.py
└── requirements.txt
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   Create a `.env` file in the root directory:
   ```
   DB_NAME=erickvale
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5433
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Collect static files:
   ```bash
   python manage.py collectstatic
   ```

5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Dream Blue (internal)

Private operational / BI surface: property intelligence, digests, and **GrantScout** (grants, incentives, regulatory signals — Bemidji / Beltrami / MN focus). You can **fill runs by hand in admin** or run the **LLM agent** (`grantscout_run_agent`) with `OPENAI_API_KEY`, **`ANTHROPIC_API_KEY` (Claude)**, or `PERPLEXITY_API_KEY` — set `GRANTSCOUT_LLM_PROVIDER` accordingly (see `.env.example`).

### URLs (staff only)

- Dashboard: `/apps/dream-blue/grantscout/`
- JSON (latest **completed** run): `/apps/dream-blue/api/grantscout/latest.json`
- Admin: **GrantScout runs / opportunities / drift** under Django admin

### Environment variables

See `.env.example` for placeholders. Required for sending digests:

| Variable | Purpose |
|----------|---------|
| `DREAM_BLUE_REPORT_RECIPIENTS` | Comma-separated To: addresses |
| `RESEND_API_KEY` + `RESEND_FROM_EMAIL` | Send via Resend |
| *or* `EMAIL_HOST` + `DEFAULT_FROM_EMAIL` (+ SMTP fields) | Send via SMTP |
| `OPENAI_API_KEY` | GrantScout agent when `GRANTSCOUT_LLM_PROVIDER=openai` (JSON mode) |
| `ANTHROPIC_API_KEY` | GrantScout agent when `GRANTSCOUT_LLM_PROVIDER=anthropic` (Claude Messages API) |
| `GRANTSCOUT_LLM_PROVIDER=perplexity` + `PERPLEXITY_API_KEY` | Perplexity **sonar** (live web / citations) |

Never commit real recipients or API keys; use `.env` on the server only.

### Management commands

```bash
# GrantScout: call LLM, save a completed run + opportunities (and drift vs previous run)
python manage.py grantscout_run_agent --dry-run   # no DB write
python manage.py grantscout_run_agent --period 2026-04

# Preview digest recipients (no send)
python manage.py dream_blue_send_digest --dry-run

# Send monthly HTML digest (includes GrantScout section if a completed run exists)
python manage.py dream_blue_send_digest
```

The agent only keeps opportunities with **valid https** `source_url` values. **Perplexity** is usually best for live web + citations. **Claude** and **OpenAI** use training knowledge and must follow the prompt to use real URLs—always verify deadlines on official pages.

### Deployment (DigitalOcean Ubuntu, user `erickvale`, project under `~`)

After `git pull` in the project directory:

```bash
source /path/to/venv/bin/activate   # if used
pip install -r requirements.txt    # when dependencies change
python manage.py migrate
python manage.py collectstatic --noinput   # if you serve static via whitenoise/collect
sudo systemctl restart gunicorn            # or your unit name for uwsgi/gunicorn
```

**Example cron** (first day of month — adjust paths; run agent before digest if you want fresh opportunities in the email):

```cron
15 7 1 * * cd /home/erickvale/erickvale && /home/erickvale/erickvale/venv/bin/python manage.py grantscout_run_agent >> /home/erickvale/logs/grantscout.log 2>&1
30 7 1 * * cd /home/erickvale/erickvale && /home/erickvale/erickvale/venv/bin/python manage.py dream_blue_send_digest >> /home/erickvale/logs/dream_blue_digest.log 2>&1
```

The digest uses the latest **completed** GrantScout run (from the agent or admin).

## Apps

### Emergency Preparedness (December 2025)
Spatial risk analysis and Point of Distribution (POD) location optimization for emergency planning in Minnesota.

### Blog
Monthly app coverage, development insights, and technical articles.

## Documentation

See the `docs/` directory for detailed documentation:
- `DJANGO_PROJECT_PROMPT.md` - Original project requirements
- `POD_OPTIMIZATION_IMPROVEMENTS.md` - POD optimization improvements
- `TESTING_GUIDE.md` - Testing instructions
- And more...



