# Chess Trainer App - Deployment

## Quick deploy (server already set up)

SSH into your server and run:

```bash
cd /home/erickvale/erickvale
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate chess_trainer
python manage.py loaddata chess_trainer/fixtures/openings.json
python manage.py collectstatic --noinput
sudo systemctl restart erickvale
```

## Verify

- **Dashboard:** https://erickvale.com/chess/
- **Homepage link:** Chess Trainer appears in the top nav

## Fixtures (first-time only)

The openings and lessons are loaded via:

```bash
python manage.py loaddata chess_trainer/fixtures/openings.json
```

If you re-run this after data exists, it may create duplicates. For a clean reset:

```bash
python manage.py shell
```

```python
from chess_trainer.models import Opening, Lesson
Lesson.objects.all().delete()
Opening.objects.all().delete()
exit()
```

Then load the fixture again.

## Troubleshooting

**Migrations:**
```bash
python manage.py showmigrations chess_trainer
```

**Logs:**
```bash
sudo journalctl -u erickvale -f
```
