# KaramSetu Backend

KaramSetu is a FastAPI backend for a hyperlocal worker and local jobs platform. This repository is API-first and structured to support the existing HTML pages plus future product surfaces.

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

## Render deployment

For a Render-only setup, deploy this repository as a single Render web service. The FastAPI app serves the API and the existing HTML pages from the same public origin.

Recommended backend environment variables:

```env
APP_NAME=KaramSetu API
APP_ENV=production
BACKEND_URL=https://your-service.onrender.com
FRONTEND_URL=https://your-service.onrender.com
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-service.onrender.com/auth/google/callback
JWT_SECRET_KEY=generate-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
MAP_GEOCODER_PROVIDER=nominatim
NOMINATIM_BASE_URL=https://nominatim.openstreetmap.org
CORS_ORIGINS=https://your-service.onrender.com
OTP_CODE_LENGTH=6
OTP_TTL_SECONDS=300
OTP_RESEND_COOLDOWN_SECONDS=60
OTP_TEST_BYPASS_CODE=123456
EMAIL_OTP_PROVIDER=mock
PHONE_OTP_PROVIDER=mock
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=KaramSetu
SMTP_USE_TLS=true
MSG91_AUTH_KEY=
MSG91_TEMPLATE_ID=
```

Use this Google OAuth Authorized redirect URI:

```text
https://your-service.onrender.com/auth/google/callback
```

If you also use local development, add:

```text
http://localhost:8000/auth/google/callback
```

The current app serves these frontend pages directly:

- `/` -> `homepage.html`
- `/find-workers` -> `find_workers.html`
- `/worker-profile` -> `worker_profile.html`

## OTP setup

The app now supports two OTP channels at the same time:

- email OTP through SMTP, controlled by `EMAIL_OTP_PROVIDER`
- phone OTP through MSG91, controlled by `PHONE_OTP_PROVIDER`

Recommended setup:

1. For email OTP:
   - set `EMAIL_OTP_PROVIDER=smtp`
   - configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`
2. For phone OTP in India:
   - set `PHONE_OTP_PROVIDER=msg91`
   - create an MSG91 OTP template and copy its `template_id`
   - copy your MSG91 auth key from the dashboard
   - set `MSG91_AUTH_KEY` and `MSG91_TEMPLATE_ID`
3. For local testing:
   - use `EMAIL_OTP_PROVIDER=mock`
   - use `PHONE_OTP_PROVIDER=mock`
   - the app returns `OTP_TEST_BYPASS_CODE` in API responses
4. For Indian delivery, make sure your MSG91 OTP template and DLT setup are configured correctly in the MSG91 dashboard.

OTP is used in two product moments:

- account email verification before profile setup
- account phone verification before profile setup
- service start phone confirmation before a booking moves to `in_progress`

## Pricing intelligence

The app now exposes local pricing guidance based on active worker profiles:

- `GET /pricing-insights?category=Electrician&city=Delhi&rate_type=daily`

The worker onboarding page and work request page both consume this endpoint to suggest local daily-rate ranges by category and city.

## OAuth note

The backend exposes the required OAuth endpoints. The callback route is scaffolded for production integration, but for local/backend-only development it currently accepts Google profile fields as query parameters so the rest of the auth and onboarding flow can be exercised before wiring the live token exchange.

## Map and geocoding note

The location module uses a provider abstraction with a development-safe mock provider. This keeps the backend compatible with Leaflet-style marker UIs now and makes it straightforward to swap in Nominatim, LocationIQ, OpenCage, or a self-hosted provider later.

## Testing

```bash
pytest
```
