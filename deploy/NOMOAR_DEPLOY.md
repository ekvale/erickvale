# NOMOAR app deployment

Inspired by [nomoar.org](https://nomoar.org/) — National Online Museum of American Racism (living archive).

## Server

```bash
cd /home/erickvale/erickvale
git pull origin main
source venv/bin/activate
python manage.py migrate nomoar
# 0006–0008: theme labels, ✊ votes; 0009: curated_related, feeds/embed; 0010: learning paths, lesson kits, glossary, commentary posts, localized packs, partner/sponsor collection fields, primary-source extras, educator newsletter signups, engagement settings; ChangeMaker.body renamed to biography (data preserved). 0011: discovery — timeline/map filters (year range, tag, theme), Start here page (`/start/`), glossary cross-terms, search snippets, related blocks on glossary/hero/commentary. 0012: optional **Event photos** (gallery per event; uploads under `media/nomoar/event_photos/`).
# Map uses event_type (violence/policy/legislation/discrimination); seed sets colors.
python manage.py loaddata nomoar/fixtures/initial.json
python manage.py collectstatic --noinput
sudo systemctl restart erickvale
```

**Map:** Set `latitude` and `longitude` (WGS84) on each `HistoricalEvent` in admin to plot it. Seed fixture includes coords. Markers **cluster** when they overlap (e.g. several in D.C.)—zoom in or click a cluster to see all pins.

If the map legend shows fewer plotted events than expected (seed = **18**), the DB is missing rows or coordinates. Prefer:

```bash
python manage.py nomoar_seed_from_fixture
```

That upserts `HistoricalEvent`, `SiteStat`, and **`ChangeMaker`** (heroes, including Native American change makers with **related timeline events**) from `nomoar/fixtures/initial.json` by slug/key (no PK conflicts). You can still use `loaddata` for a clean install; use `nomoar_sync_coords` only to refresh lat/lng on existing rows without changing other fields.

**Sample engagement content** (learning path, lesson kit, glossary, commentary, localized pack, demo collections, poster PDFs, test newsletter rows, sample primary source):

```bash
python manage.py nomoar_seed_sample_content
```

Run after `migrate` and `nomoar_seed_from_fixture`. Copies `nomoar/static/nomoar/samples/sample-poster.pdf` into Media for the lesson kit and localized pack when those files are empty. Static poster template: `nomoar/static/nomoar/samples/sample-poster.svg` (served after `collectstatic`).

**Logo:** `nomoar/static/nomoar/NOMOARLogo.jpg` is collected to static; ensure it exists after pull.

If Django reports `Unknown command: 'nomoar_seed_from_fixture'`, your server copy is missing `nomoar/management/commands/` — run `git pull` after the repo has been updated (those files must be committed and pushed).

Uses [Leaflet](https://leafletjs.com/) + [MarkerCluster](https://github.com/Leaflet/Leaflet.markercluster) + CARTO dark tiles.

## URLs

- **Home:** `/apps/nomoar/`
- **Timeline:** `/apps/nomoar/Timeline/` — filters: `?decade=2020s`, `?type=`, `?state=` (2-letter), `?q=` (Postgres: full-text; SQLite: icontains). Deep-link an entry: `?focus=<event-slug>`. **Copy link to filters** copies the current query string.
- **Map:** `/apps/nomoar/Map/` — optional `?focus=<slug>` flies to that marker and opens the popup. Popups link **On timeline** to the same focus URL. Filter markers: `?year_from=`, `?year_to=`, `?type=` (same values as timeline event type), `?q=` (full-text / icontains). **Copy map link** preserves the current query string.
- **Heroes & change makers:** `/apps/nomoar/Heroes/`
- **Hero profile:** `/apps/nomoar/HeroDetail/<slug>/`
- **Event:** `/apps/nomoar/EventDetail/<slug>/`
- **Submit:** `/apps/nomoar/Submit/`
- **Educators / Support:** `/apps/nomoar/Educators/` (lesson kits, paths, partner spotlights, RSS/JSON, **POST** digest signup `/apps/nomoar/Educators/subscribe/`), `/apps/nomoar/Pricing/` (reads **Engagement & support settings** from admin).
- **Learning paths:** `/apps/nomoar/paths/`, `/apps/nomoar/paths/<slug>/`
- **Collections (public):** `/apps/nomoar/collections/`, `/apps/nomoar/collections/<slug>/` — partner org, guest byline, sponsor disclosure fields in admin
- **Lesson kits:** `/apps/nomoar/lesson-kits/`, `/apps/nomoar/lesson-kits/<slug>/` (optional PDF upload)
- **What is new:** `/apps/nomoar/whats-new/` (recent `updated_at`; pair with RSS/JSON feeds)
- **Glossary:** `/apps/nomoar/glossary/`, `/apps/nomoar/glossary/<slug>/`
- **Places index:** `/apps/nomoar/places/` → timeline `?location=…`
- **Commentary:** `/apps/nomoar/commentary/`, `/apps/nomoar/commentary/<slug>/`
- **Localized packs:** `/apps/nomoar/packs/`, `/apps/nomoar/packs/<slug>/` (embed hints + optional PDF)
- **Feeds / embed:** `feed/events.xml`, `feed/events.json`, `Embed/Event/<slug>/`, `Embed/slice/` (supports `location=` like timeline)

**Env (optional):** `NOMOAR_CORRECTIONS_EMAIL` — shown in the site-wide educational disclaimer and on event pages for reporting corrections.

Admin: `HistoricalEvent` (inline **Event sources** — kind, context note, attachment, media URL; plus **Theme labels**, **Tags**, **Curated related**), `EventThemeLabel`, `ChangeMaker` (**Biography**, **Related events**), `SiteStat`, `Collection` (partner spotlight + sponsor disclosure), `Tag`, `LearningPath` + inline steps, `LessonKit`, `GlossaryTerm`, `ArchiveNewsPost`, `LocalizedResourcePack`, `NewsletterSubscriber`, **Engagement & support settings** (singleton).

**API:** `POST /apps/nomoar/api/event/<slug>/fist/` toggles one raised-fist per browser session (CSRF + session cookie). Timeline and event detail use this for the ✊ control.
