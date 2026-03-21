# NOMOAR app deployment

Inspired by [nomoar.org](https://nomoar.org/) — National Online Museum of American Racism (living archive).

## Server

```bash
cd /home/erickvale/erickvale
git pull origin main
source venv/bin/activate
python manage.py migrate nomoar
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

That upserts `HistoricalEvent`, `SiteStat`, and **`ChangeMaker`** (heroes) from `nomoar/fixtures/initial.json` by slug/key (no PK conflicts). You can still use `loaddata` for a clean install; use `nomoar_sync_coords` only to refresh lat/lng on existing rows without changing other fields.

**Logo:** `nomoar/static/nomoar/NOMOARLogo.jpg` is collected to static; ensure it exists after pull.

If Django reports `Unknown command: 'nomoar_seed_from_fixture'`, your server copy is missing `nomoar/management/commands/` — run `git pull` after the repo has been updated (those files must be committed and pushed).

Uses [Leaflet](https://leafletjs.com/) + [MarkerCluster](https://github.com/Leaflet/Leaflet.markercluster) + CARTO dark tiles.

## URLs

- **Home:** `/apps/nomoar/`
- **Timeline:** `/apps/nomoar/Timeline/` (decade pills `?decade=2020s`, search `?q=`)
- **Map:** `/apps/nomoar/Map/`
- **Heroes & change makers:** `/apps/nomoar/Heroes/`
- **Hero profile:** `/apps/nomoar/HeroDetail/<slug>/`
- **Event:** `/apps/nomoar/EventDetail/<slug>/`
- **Submit:** `/apps/nomoar/Submit/`
- **Educators / Support:** `/apps/nomoar/Educators/`, `/apps/nomoar/Pricing/`

Admin: add/edit `HistoricalEvent`, `ChangeMaker`, `SiteStat`, `Collection`, `Tag`.
