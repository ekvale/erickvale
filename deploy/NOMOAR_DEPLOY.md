# NOMOAR app deployment

Inspired by [nomoar.org](https://nomoar.org/) — National Online Museum of American Racism (living archive).

## Server

```bash
cd /home/erickvale/erickvale
git pull origin main
source venv/bin/activate
python manage.py migrate nomoar
python manage.py loaddata nomoar/fixtures/initial.json
python manage.py collectstatic --noinput
sudo systemctl restart erickvale
```

**Map:** Set `latitude` and `longitude` (WGS84) on each `HistoricalEvent` in admin to plot it. Seed fixture includes coords. The map uses [Leaflet](https://leafletjs.com/) + CARTO dark basemap; hover = tooltip, click = popup with summary and link.

## URLs

- **Home:** `/apps/nomoar/`
- **Timeline:** `/apps/nomoar/Timeline/`
- **Map:** `/apps/nomoar/Map/`
- **Event:** `/apps/nomoar/EventDetail/<slug>/`
- **Submit:** `/apps/nomoar/Submit/`
- **Educators / Support:** `/apps/nomoar/Educators/`, `/apps/nomoar/Pricing/`

Admin: add/edit `HistoricalEvent`, `SiteStat`, `Collection`, `Tag`.
