# Django Emergency Preparedness App - Project Prompt

## Project Overview
Create a Django application called `emergency_preparedness` as part of a larger Django project named `erickvale`. This app will provide spatial risk analysis and Point of Distribution (POD) location optimization for emergency planning in Minnesota, using Leaflet.js for interactive mapping.

## Project Structure
```
erickvale/
├── manage.py
├── erickvale/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── emergency_preparedness/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── serializers.py (if using DRF)
│   ├── admin.py
│   ├── migrations/
│   ├── templates/
│   │   └── emergency_preparedness/
│   │       └── index.html
│   └── static/
│       └── emergency_preparedness/
│           ├── css/
│           │   └── style.css
│           └── js/
│               └── app.js
├── demographic_data.json
└── requirements.txt
```

## Core Requirements

### 1. Data Models

#### POD Model
Create a `POD` model with the following fields:
- `id`: Auto-incrementing primary key
- `name`: CharField (max_length=200, required)
- `latitude`: DecimalField (max_digits=9, decimal_places=6)
- `longitude`: DecimalField (max_digits=9, decimal_places=6)
- `coverage_radius`: FloatField (default=50.0) - in kilometers
- `occupancy`: IntegerField (default=0) - capacity
- `parking_lot_size`: FloatField (default=0.0) - in acres
- `acreage`: FloatField (default=0.0) - total acreage
- `status`: CharField with choices: 'proposed', 'active', 'inactive' (default='proposed')
- `points_covered`: IntegerField (default=0) - calculated field
- `total_risk_covered`: FloatField (default=0.0) - calculated field
- `total_population_covered`: IntegerField (default=0) - calculated field
- `avg_drive_time`: FloatField (default=0.0) - in minutes
- `max_drive_time`: FloatField (default=0.0) - in minutes
- `created_at`: DateTimeField (auto_now_add=True)
- `updated_at`: DateTimeField (auto_now=True)

#### Scenario Model
Create a `Scenario` model with the following fields:
- `id`: Auto-incrementing primary key
- `name`: CharField (max_length=200, required)
- `description`: TextField (blank=True)
- `type`: CharField with choices: 'general', 'pandemic', 'natural_disaster', 'severe_weather', 'infrastructure_failure' (default='general')
- `severity`: FloatField (default=1.0, validators: min=0.5, max=3.0)
- `affected_areas`: JSONField or TextField (store as comma-separated or JSON array)
- `created_at`: DateTimeField (auto_now_add=True)
- `updated_at`: DateTimeField (auto_now=True)

#### ScenarioPOD Model (Many-to-Many relationship)
Create a `ScenarioPOD` model to link scenarios with PODs:
- `scenario`: ForeignKey to Scenario
- `pod`: ForeignKey to POD
- `created_at`: DateTimeField (auto_now_add=True)

### 2. Minnesota Boundary Constraints
Implement boundary validation functions:
- Minnesota bounds: Latitude 43.0° to 49.5°, Longitude -97.5° to -89.0°
- Create utility functions to validate and constrain coordinates within Minnesota
- Apply validation in model clean() methods and API serializers

### 3. Demographic Data Integration
- Load demographic data from `demographic_data.json` containing 47+ Minnesota cities
- Each city entry has: name, lat, lon, population, county
- Use this data for risk score calculations and POD optimization

### 4. Risk Score Calculation
Implement risk score calculation based on demographic data:
- Formula: `Risk = (Population Density/2000 × 0.4) + (Hazard × 0.3) + ((1-Infrastructure) × 0.3)`
- Population density calculated from city population and estimated area
- Hazard and infrastructure scores generated based on population size
- All risk scores normalized to 0-1 range

### 5. POD Optimization Algorithm
Implement a greedy algorithm to find optimal POD locations:
1. Load demographic data and calculate risk scores
2. Sort cities by (Population × Risk Score) descending
3. For each POD to place:
   - Evaluate top 30 candidate cities
   - Calculate coverage score: `(Population × 0.5) + (Risk × 1000 × 0.3) + ((Max Drive Time - Avg Drive Time) × 10 × 0.2)`
   - Select highest scoring location
   - Remove nearby candidates (within 30km) to prevent clustering
4. Return optimal POD locations with coverage statistics

### 6. Drive Time Calculation
Implement drive time calculation with two methods:
- **Primary**: OpenRouteService API integration (optional, via environment variable `ORS_API_KEY`)
- **Fallback**: Distance-based estimation using Haversine formula and average speed (60 km/h)
- Calculate average and maximum drive times for POD coverage areas

### 7. Scenario-Specific Risk Modifications
Implement scenario risk modifications:
- **Pandemic**: `Risk × (1 + (Population/500000) × Severity)` - affects all areas, more in high-density
- **Natural Disaster**: `Risk × (1 + Severity × 0.5)` - for specified affected areas only
- **Severe Weather**: `Risk × (1 + (1-Infrastructure) × Severity × 0.3)` - based on infrastructure vulnerability
- **Infrastructure Failure**: `Risk × (1 + (1-Infrastructure) × Severity × 0.4)` - significant impact on poor infrastructure areas

### 8. API Endpoints (REST API)

#### POD Endpoints
- `GET /api/pods/` - List all PODs
- `POST /api/pods/` - Create new POD
- `GET /api/pods/{id}/` - Get specific POD
- `PUT /api/pods/{id}/` - Update POD
- `PATCH /api/pods/{id}/` - Partial update POD
- `DELETE /api/pods/{id}/` - Delete POD
- `GET /api/pods/optimal/` - Generate optimal PODs (query params: `num_pods`, `max_drive_time`)

#### Scenario Endpoints
- `GET /api/scenarios/` - List all scenarios
- `POST /api/scenarios/` - Create new scenario
- `GET /api/scenarios/{id}/` - Get specific scenario (include associated PODs)
- `PUT /api/scenarios/{id}/` - Update scenario
- `PATCH /api/scenarios/{id}/` - Partial update scenario
- `DELETE /api/scenarios/{id}/` - Delete scenario
- `GET /api/scenarios/{id}/risk-data/` - Get scenario-modified risk data
- `GET /api/scenarios/{id}/analyze/` - Analyze scenario coverage

#### Other Endpoints
- `GET /api/demographic-data/` - Get demographic data
- `GET /api/risk-data/` - Get base risk data (or scenario-specific if scenario_id provided)
- `POST /api/drive-time/` - Calculate drive time between two points

### 9. Frontend Requirements

#### HTML Template (index.html)
- Main map container using Leaflet.js
- Control panel with:
  - Number of PODs input (1-20)
  - Max drive time input (10-120 minutes)
  - Generate Optimal PODs button
  - Add POD button
  - Add Scenario button
  - Active Scenario dropdown
  - Analyze Scenario button
  - Toggle checkboxes for risk points and coverage areas
  - "How Optimization Works" info button
- Tabbed sidebar with:
  - PODs tab: List of all PODs with details
  - Scenarios tab: List of all scenarios
- Modal forms for:
  - POD creation/editing
  - Scenario creation/editing
  - Optimization algorithm explanation

#### JavaScript (app.js)
- Initialize Leaflet map centered on Minnesota (46.7296, -94.6859, zoom 6)
- Implement Leaflet.markercluster for grouping markers
- Risk points layer with color-coded markers (green to red based on risk score)
- POD markers layer with numbered markers
- Coverage circles layer showing POD coverage areas
- Functions for:
  - Loading and displaying risk data
  - Loading and displaying PODs
  - Loading and displaying scenarios
  - Creating/editing/deleting PODs
  - Creating/editing/deleting scenarios
  - Generating optimal PODs
  - Analyzing scenarios
  - Switching active scenarios
  - Tab navigation
- Event handlers for all UI interactions
- API integration using fetch()

#### CSS (style.css)
- Modern, responsive design with gradient header
- Sidebar with tabs
- Modal styling
- POD and scenario list item cards
- Form styling
- Marker cluster customization
- Color scheme: Purple gradient (#667eea to #764ba2)

### 10. Key Features to Implement

#### Marker Clustering
- Use Leaflet.markercluster plugin
- Risk points cluster when zoomed out, ungroup when zoomed in
- PODs also use clustering
- Custom cluster styling with color-coded sizes

#### Scenario Planning
- Create scenarios with different types and severity levels
- Associate PODs with scenarios
- View scenario-specific risk data on map
- Analyze scenario coverage effectiveness
- Compare scenarios side-by-side

#### Data Persistence
- Use Django models and database (SQLite for development, PostgreSQL recommended for production)
- No need for JSON file storage - use database
- Implement proper migrations

### 11. Dependencies
Add to requirements.txt:
```
Django>=4.2.0
djangorestframework>=3.14.0  # If using DRF
requests>=2.31.0
python-decouple>=3.8  # For environment variables
```

### 12. Settings Configuration
In `erickvale/settings.py`:
- Add `emergency_preparedness` to INSTALLED_APPS
- Configure static files and media files
- Set up CORS if needed for API access
- Add environment variable support for ORS_API_KEY

### 13. URL Configuration
- Main app view at `/` (or `/emergency/`)
- API endpoints under `/api/`
- Include emergency_preparedness URLs in main project urls.py

### 14. Admin Interface
- Register POD and Scenario models in admin.py
- Provide admin interface for managing data
- Include filters and search functionality

### 15. Validation and Error Handling
- Validate coordinates are within Minnesota bounds
- Constrain coordinates to Minnesota if outside bounds
- Handle API errors gracefully
- Provide user-friendly error messages

### 16. Testing Considerations
- Unit tests for risk score calculations
- Unit tests for POD optimization algorithm
- Unit tests for scenario risk modifications
- Integration tests for API endpoints
- Frontend tests for key interactions

### 17. Documentation
- Include comprehensive docstrings for all functions
- Document API endpoints with expected request/response formats
- Update README with Django-specific setup instructions
- Document environment variables needed

## Implementation Notes

1. **Use Django REST Framework** for API endpoints if possible, or implement JSON responses with standard Django views
2. **Use Django's JSONField** for storing affected_areas array in Scenario model
3. **Implement model methods** for coverage calculations rather than doing it in views
4. **Use Django signals** if needed for automatic coverage recalculation when PODs are updated
5. **Consider caching** for demographic data and risk calculations if performance becomes an issue
6. **Use Django's template system** for the main HTML, but keep JavaScript and CSS in static files
7. **Implement proper authentication/authorization** if this is part of a larger system
8. **Use Django's management commands** for loading initial demographic data

## Expected Behavior

- Users can create, edit, and delete PODs through the web interface
- Users can generate optimal POD locations based on demographics and drive times
- Users can create emergency scenarios and associate PODs with them
- Users can view scenario-specific risk data on the interactive map
- Users can analyze scenario coverage to see effectiveness metrics
- All markers cluster when zoomed out for better performance
- Risk points are color-coded based on risk scores
- POD coverage areas are visualized as circles on the map
- All coordinates are validated to stay within Minnesota boundaries

## Success Criteria

The Django app should replicate all functionality of the Flask version:
- ✅ POD CRUD operations
- ✅ Optimal POD generation algorithm
- ✅ Scenario planning and management
- ✅ Scenario-specific risk calculations
- ✅ Drive time calculations
- ✅ Interactive Leaflet map with clustering
- ✅ Demographic data integration
- ✅ Minnesota boundary validation
- ✅ Coverage analysis and statistics

