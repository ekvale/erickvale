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



