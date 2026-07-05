# KaamSetu Backend

KaamSetu is a FastAPI backend for a hyperlocal worker and local jobs platform. This repository is API-first and structured to support the existing HTML pages plus future product surfaces.

## Stack

- Python 3.11
- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL on Neon compatible configuration
- Pydantic v2
- JWT auth
- Google OAuth-ready callback flow abstraction

## Structure

```text
app/
  admin/ auth/ bookings/ common/ contractor/ core/ disputes/ location/
  notifications/ operator/ profiles/ reviews/ users/ verification/
  workers/ work_requests/
```

## Setup

1. Create and activate a Python 3.11 virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and update:

- `DATABASE_URL` with your Neon PostgreSQL URL, for example `postgresql+psycopg://user:pass@host/dbname?sslmode=require`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `JWT_SECRET_KEY`

4. Run migrations:

```bash
alembic upgrade head
```

5. Seed initial data:

```bash
python scripts/seed_data.py
```

6. Start the API:

```bash
uvicorn app.main:app --reload
```

Swagger docs are available at `/docs`. Health is at `/health`.

## OAuth note

The backend exposes the required OAuth endpoints. The callback route is scaffolded for production integration, but for local/backend-only development it currently accepts Google profile fields as query parameters so the rest of the auth and onboarding flow can be exercised before wiring the live token exchange.

## Map and geocoding note

The location module uses a provider abstraction with a development-safe mock provider. This keeps the backend compatible with Leaflet-style marker UIs now and makes it straightforward to swap in Nominatim, LocationIQ, OpenCage, or a self-hosted provider later.

## Testing

```bash
pytest
```
