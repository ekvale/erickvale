# Arm Chair Detective

A realistic detective investigation game for the erickvale Django project. Players start with a large suspect pool, receive clues (eyewitness accounts, 911 calls, video analysis), and use filters to narrow down until they identify the perpetrator.

## Setup

1. **Generate suspect pool** (required before playing):
   ```bash
   python manage.py generate_suspects --count 100000   # 100K suspects (~20 sec)
   python manage.py generate_suspects --count 1000000  # 1M suspects (~4 min)
   ```

2. **Create a case**:
   ```bash
   python manage.py create_sample_case
   # Or with options:
   python manage.py create_sample_case --case-title "The Jewel Heist" --difficulty hard
   python manage.py create_sample_case --perpetrator-id 12345  # Use specific suspect
   ```

3. **Play**: Visit `/apps/arm-chair-detective/`

## Scaling to 1M Suspects

- PostgreSQL handles 1M rows well with indexed filter fields.
- Use `--batch 5000` (default) or `10000` for faster bulk creation.
- All filterable attributes (`gender`, `hair_color`, `vehicle_type`, etc.) are indexed.
- Filtering 1M suspects typically returns in &lt;1 second with proper indexes.

## Clue Types

- **Eyewitness Account** – physical description (hair, eyes, build, height)
- **911 Call Transcript** – gender, vehicle, accent
- **Video Footage Analysis** – comprehensive physical + vehicle details
- **License Plate Fragment** – partial plate + vehicle
- **Cell Tower / Location Data** – movement patterns, occupation hints
- **Financial Records** – transactions, vehicle cross-ref
- **Social Media / Digital Footprint** – accent, regional markers
- **Employer / Employment Records** – occupation
- **Statement / Linguistic Analysis** – accent, hedging, reliability
- **Audio Transcript** – 911/voicemail with accent, tone, hesitations

## Timeline Pressure

Clues can have `unlock_after_hours` – they only become available after advancing the case timeline. Use "Advance Time (+12 hours)" to unlock time-gated clues.
