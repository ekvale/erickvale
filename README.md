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

**Stored reports:** Each completed agent run saves **`compiled_report`** (Markdown-style text) and **`agent_snapshot`** (full JSON payload) on `GrantScoutRun`, plus rows in `GrantScoutOpportunity`. View in Django admin under the run.

**Monthly HTML digest** (`dream_blue_send_digest`) includes: business **calendar** (leases, loans, utilities, taxes, maintenance, etc.), **KPI** table, **narrative report sections**, **lease roster**, **loan schedule** (with payoff/refi fields where set), **utility accounts**, optional **lease comp research** memo (latest completed run), optional **GrantScout** block (latest completed run), and **lease economics**: monthly cash out (operating + loans), rent collected, **breakeven gross potential rent** using an assumed **economic vacancy** rate, **implied value band** from trailing **NOI** and a default **8%–10% cap rate** range (configurable), optional extra **$/sf/year** benchmark. **Suggested asking rents** per unit use above-grade + below-grade storage sf on each lease row, configurable $/sf rates, and location factors (e.g. corner + kitchen vs inline retail). Fields: `square_footage`, `square_footage_storage`.

#### Make report storage live (server)

```bash
cd ~/erickvale
git pull
source venv/bin/activate   # if you use a venv
pip install -r requirements.txt   # if dependencies changed
python manage.py migrate
sudo systemctl restart gunicorn   # or your app service — loads new code
```

**Smoke test (optional, uses API credits):**

```bash
python manage.py grantscout_run_agent --dry-run
python manage.py grantscout_run_agent --period "$(date +%Y-%m)"
```

In **Admin → GrantScout runs →** open the new run: confirm **Stored report** shows **compiled_report** and **agent_snapshot**, and **Opportunities** inline matches. Old runs created before this migration have empty `compiled_report` / `agent_snapshot` until you re-run the agent or leave them as-is.

**Digest shows “No completed GrantScout run” but you ran the agent:** The email only includes runs with **Status = Completed**. The digest command must use the **same database** as `grantscout_run_agent` (same `manage.py` on the server, project directory so `.env` / `DB_*` match). From `~/erickvale` after `source venv/bin/activate`, check:

```bash
python manage.py shell -c "from dream_blue.models import GrantScoutRun; from dream_blue.digest_context import get_latest_completed_grantscout_run; print('runs', list(GrantScoutRun.objects.values_list('id','period_label','status'))); print('latest_completed', get_latest_completed_grantscout_run())"
```

If you see runs but `latest_completed` is `None`, open the run in **Admin** and set status to **Completed**, or re-run `grantscout_run_agent`. When you send the digest, the command prints whether it found a run (`GrantScout: using run id=…`) or a warning with counts.

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
| `GRANTSCOUT_ANTHROPIC_MODEL` | Optional; default `claude-sonnet-4-6`. Old ids (e.g. `claude-3-5-sonnet-*`) may 404 — check [Anthropic models](https://docs.anthropic.com/en/docs/about-claude/models/overview). |
| `GRANTSCOUT_LLM_PROVIDER=perplexity` + `PERPLEXITY_API_KEY` | Perplexity **sonar** (live web / citations) |
| `DREAM_BLUE_LEASE_ECONOMICS_VACANCY_PCT` | Economic vacancy % for breakeven GPR in digest (default `8`) |
| `DREAM_BLUE_CAP_RATE_BENCHMARK_LOW` / `DREAM_BLUE_CAP_RATE_BENCHMARK_HIGH` | Cap rate band (default `8` / `10`, whole percents) for implied value from trailing NOI |
| `DREAM_BLUE_SUGGEST_RENT_PSF_YEAR_ABOVE` / `DREAM_BLUE_SUGGEST_RENT_PSF_YEAR_STORAGE` | Digest suggested asking rent: above-grade $/sf/yr and storage $/sf/yr (defaults `9.5` / `2`) |
| `DREAM_BLUE_RENT_BENCHMARK_PSF_YEAR` | Optional extra market gross $/sf/yr vs breakeven required $/sf |
| `DREAM_BLUE_RENT_BENCHMARK_NOTE` | Short note (gross vs NNN, source, date) for optional $/sf benchmark |

Never commit real recipients or API keys; use `.env` on the server only.

### Management commands

```bash
# GrantScout: call LLM, save a completed run + opportunities (and drift vs previous run)
python manage.py grantscout_run_agent --dry-run   # no DB write
python manage.py grantscout_run_agent --period 2026-04

# Lease comparables memo (Bemidji-area); saves LeaseCompResearchRun with diff vs prior completed memo
python manage.py dream_blue_run_lease_comp_agent --dry-run
python manage.py dream_blue_run_lease_comp_agent

# Preview digest recipients (no send)
python manage.py dream_blue_send_digest --dry-run

# Send monthly HTML digest (includes GrantScout section if a completed run exists)
python manage.py dream_blue_send_digest
```

The agent keeps opportunities whose **`source_url` passes a quick HTTP check** (GET with a browser-like `User-Agent`, follow redirects; **404/5xx are dropped**). Tuning: `GRANTSCOUT_URL_CHECK_TIMEOUT`, `GRANTSCOUT_URL_CHECK_DELAY_SEC`, or `GRANTSCOUT_VALIDATE_SOURCE_URLS=False` / `python manage.py grantscout_run_agent --skip-url-check` to skip checks (faster; more bad links). **Perplexity** is usually best for live web + citations. **Claude**/**OpenAI** should prefer **hub/index** URLs when a deep link is uncertain—always spot-check deadlines on official pages.

### Deployment (DigitalOcean Ubuntu, user `erickvale`, project under `~`)

After `git pull` in the project directory:

```bash
source /path/to/venv/bin/activate   # if used
pip install -r requirements.txt    # when dependencies change
python manage.py migrate
# If Dream Blue shows conflicting migrations, merge then migrate — merge files do not add columns; skipping migrate causes errors like missing rent_basis.
python manage.py collectstatic --noinput   # if you serve static via whitenoise/collect
sudo systemctl restart gunicorn            # or your unit name for uwsgi/gunicorn
```

**GrantScout every two weeks + digest email:** `deploy/grantscout_agent_biweekly.sh` runs daily from cron but **skips** the agent until `GRANTSCOUT_INTERVAL_DAYS` (default **14**) have passed since the last successful run (state file under `~/.cache`). After each successful `grantscout_run_agent`, it runs **`dream_blue_send_digest`** so recipients get the HTML email (override with `GRANTSCOUT_SEND_DIGEST=0` if needed).

```bash
chmod +x deploy/grantscout_agent_biweekly.sh
mkdir -p ~/logs
```

```cron
# 07:15 UTC daily; script only runs agent when 14+ days since last success
15 7 * * * /home/erickvale/erickvale/deploy/grantscout_agent_biweekly.sh >> /home/erickvale/logs/grantscout.log 2>&1
```

Adjust `GRANTSCOUT_INTERVAL_DAYS`, `GRANTSCOUT_STATE`, or `GRANTSCOUT_PYTHON` if your paths differ.

**Lease comp on a schedule (monthly or quarterly):** `deploy/lease_comp_scheduled.sh` mirrors the GrantScout pattern — daily cron, but the agent runs only after `LEASE_COMP_INTERVAL_DAYS` (default **30**; use **90** for quarterly). After a successful run it can trigger `dream_blue_send_digest` (`LEASE_COMP_SEND_DIGEST=1`, default).

```bash
chmod +x deploy/lease_comp_scheduled.sh
# 07:20 UTC daily; script skips until interval elapsed
20 7 * * * /home/erickvale/erickvale/deploy/lease_comp_scheduled.sh >> /home/erickvale/logs/lease_comp.log 2>&1
```

**Staff tools (login + staff flag):** [Operations calendar](/apps/dream-blue/operations/calendar/), [units / $·sf dashboard](/apps/dream-blue/operations/units/), **[rollover & vacancy command center](/apps/dream-blue/operations/rollover/)** (pipeline stages + NOI-priority sort), [ICS calendar feed](/apps/dream-blue/operations/calendar.ics) (add `?critical=1` for leases, property tax, and insurance only — useful for Google Calendar “subscribe by URL”). The HTML digest includes a short **Money moves** block (top N rows; `DREAM_BLUE_MONEY_MOVES_LIMIT`).

**Digest-only on another schedule** (optional — e.g. monthly reminders without re-running the agent):

```cron
30 7 1 * * cd /home/erickvale/erickvale && ./venv/bin/python manage.py dream_blue_send_digest >> /home/erickvale/logs/dream_blue_digest.log 2>&1
```

The digest pulls calendar events, KPIs, leases, loans, utilities, and lease economics from the database; GrantScout and lease-comp sections use the latest **completed** runs for each.

## Apps

### Brain dump (personal GTD capture)
Private inbox at `/apps/braindump/` for the configured owner only (`BRAINDUMP_OWNER_USERNAME` or `BRAINDUMP_OWNER_USER_ID`). Large capture box, OpenAI categorization (`OPENAI_API_KEY`), statuses (to do / waiting / done with auto-archive), manual calendar day edits, and `python manage.py send_braindump_monthly_calendar` for an HTML month grid (uses Resend/SMTP like Dream Blue). When configured, the owner is sent to the brain dump after login and from `/` instead of the public homepage.

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



