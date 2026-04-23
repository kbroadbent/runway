# Runway

Runway is a personal job search pipeline tool. It tracks job postings from initial discovery through offer — search, review, apply, interview, and close. Single-user, no multi-tenancy.

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy ORM, SQLite, Alembic
- **Frontend:** SvelteKit 2, Svelte 5, TypeScript, Vite
- **Job scraping:** python-jobspy
- **Testing:** pytest, pytest-asyncio (backend only)

## Running Locally

```bash
./run.sh                  # starts both backend (port 8000) and frontend (port 5173)
```

Or individually:

```bash
cd backend && uvicorn app.main:app --port 8000 --reload
cd frontend && npm run dev
```

Install dependencies:

```bash
cd backend && pip install -e ".[dev]"
cd frontend && npm install
```

## Project Structure

```
backend/
  app/
    models/       # SQLAlchemy ORM models
    schemas/      # Pydantic request/response schemas
    routers/      # FastAPI route handlers
    services/     # Business logic (search, research, parsing, scheduling)
  alembic/
    versions/     # Database migration scripts

frontend/
  src/
    routes/       # SvelteKit pages (search, postings, pipeline)
    lib/
      components/ # Reusable Svelte components
```

## Database

SQLite database lives at `backend/runway.db` by default. The path is configurable via the `DATABASE_PATH` environment variable (used by Docker to store the DB at `/app/data/runway.db`).

All schema changes must go through Alembic migrations:

```bash
# Apply all pending migrations
cd backend && alembic upgrade head

# Generate a new migration after changing a model
cd backend && alembic revision --autogenerate -m "description"
```

Back up the database before risky changes:

```bash
make backup   # creates a timestamped copy in backups/
```

## Testing

```bash
cd backend && pytest
cd frontend && npm run test
```

## Key Conventions

- **Tiers:** `job_postings` has a `tier` field for priority categorization (used to filter and sort postings)
- **Lead source:** `job_postings` has a `lead_source` field tracking how the opportunity was found — `referral`, `recruiter_inbound`, `recruiter_outbound`, or `cold_apply` (default). Both postings and pipeline pages support filtering by lead source.
- **Pipeline:** stages are tracked in `pipeline_entries` with audit history — don't update in place, append new entries. Individual history records (stage transitions and manual events) can be deleted from the timeline via `DELETE /api/pipeline-history/{id}`; this is cosmetic and does not change the current pipeline stage.
- **Company research:** Glassdoor, Levels.fyi, and Blind links are stored on the `Company` model alongside other research metadata
