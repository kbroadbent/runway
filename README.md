# Runway

A personal job search pipeline tool that tracks job postings from initial discovery through offer — search, review, apply, interview, and close.

## Tech Stack

| Layer    | Technology                                        |
| -------- | ------------------------------------------------- |
| Backend  | Python, FastAPI, SQLAlchemy, Alembic              |
| Frontend | SvelteKit 2, Svelte 5, TypeScript, Vite           |
| Database | SQLite                                            |
| Scraping | python-jobspy                                     |
| AI       | LiteLLM (optional Ollama for local model support) |

## Getting Started

There are two ways to run Runway. Pick whichever suits you.

### Option A: Docker (recommended)

Requires only [Docker](https://docs.docker.com/get-docker/).

```bash
git clone <repo-url>
cd runway
cp .env.example .env
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000). Migrations run automatically on startup.

### Option B: Local Development

Requires Python (>= 3.10), Node.js, and optionally Ollama. Instructions assume macOS.

```bash
# Python
brew install python
# Or: brew install pyenv && pyenv install 3.12 && pyenv local 3.12

# Node.js
brew install node
# Or: brew install nvm && nvm install --lts && nvm use --lts

# Ollama (optional — AI-powered job parsing, falls back to heuristics without it)
brew install ollama
```

Clone and install dependencies:

```bash
git clone <repo-url>
cd runway

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cd ..

# Frontend
cd frontend
npm install
cd ..

# Database
cd backend && alembic upgrade head && cd ..
```

Start both backend and frontend:

```bash
just dev
```

- **Backend** at [http://localhost:8000](http://localhost:8000)
- **Frontend** at [http://localhost:5173](http://localhost:5173)

Ollama starts automatically if installed.

## Using an Existing Database

The database lives at `data/runway.db`. To use an existing database, copy it there before starting:

```bash
cp /path/to/your/runway.db data/runway.db
```

This works for both Docker and local development. Migrations run automatically on startup (Docker) or via `just migrate` (local).

## AI Features (Optional)

Runway uses LLM-powered parsing for job postings. Without an LLM, it falls back to heuristics.

**Ollama (local, free):** Install and run [Ollama](https://ollama.com) on your machine. Runway connects to it automatically — no configuration needed.

```bash
brew install ollama
ollama serve &
ollama pull llama3.2
```

**Cloud LLM provider:** Set your provider's API key in `.env`:

```bash
# OpenAI
AI_MODEL=gpt-4o
OPENAI_API_KEY=sk-...

# Or Anthropic
AI_MODEL=anthropic/claude-sonnet-4-20250514
ANTHROPIC_API_KEY=sk-ant-...
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

data/               # SQLite database (gitignored)
```

## Database Management

All schema changes go through Alembic migrations:

```bash
cd backend

# Apply pending migrations
alembic upgrade head

# Generate a new migration after changing a model
alembic revision --autogenerate -m "description"
```

Back up the database before risky changes:

```bash
just backup
```

## Testing

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm run test
```

## Just Commands

| Command            | Description                              |
| ------------------ | ---------------------------------------- |
| `just dev`         | Start backend and frontend (local)       |
| `just docker`      | Run Docker container                     |
| `just docker-build`| Rebuild and run Docker container         |
| `just docker-bg`   | Run Docker container in background       |
| `just docker-down` | Stop Docker container                    |
| `just migrate`     | Apply all pending Alembic migrations     |
| `just backup`      | Create a timestamped database backup     |

## Environment Variables

See `.env.example` for all options. Docker-specific paths (`DATABASE_PATH`, `STATIC_DIR`) are set in `docker-compose.yml` — don't put them in `.env`.

| Variable         | Description                              | Default                          |
| ---------------- | ---------------------------------------- | -------------------------------- |
| `CORS_ORIGINS`   | Comma-separated list of allowed origins  | `http://localhost:5173,http://localhost:8000` |
| `OLLAMA_BASE_URL`| URL of the Ollama server                 | `http://localhost:11434`         |
| `AI_MODEL`       | LLM model to use for parsing             | `ollama/llama3.2`                |
| `DATABASE_PATH`  | Path to the SQLite database file         | `data/runway.db` (set by Docker) |
| `STATIC_DIR`     | Path to built frontend static files      | Unset (set by Docker)            |
