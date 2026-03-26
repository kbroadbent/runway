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

## Prerequisites

> **Note:** These instructions assume macOS. Other platforms should work but are untested.

### Python (>= 3.10)

Install via [Homebrew](https://brew.sh):

```bash
brew install python
```

Or use a version manager like [pyenv](https://github.com/pyenv/pyenv):

```bash
brew install pyenv
pyenv install 3.12
pyenv local 3.12
```

### Node.js

Install via Homebrew:

```bash
brew install node
```

Or use a version manager like [nvm](https://github.com/nvm-sh/nvm):

```bash
brew install nvm
nvm install --lts
nvm use --lts
```

### Ollama (optional)

Ollama provides local LLM support for AI-powered job parsing. Without it, parsing falls back to heuristics.

```bash
brew install ollama
```

## Installation

Clone the repo and install dependencies for both backend and frontend:

```bash
git clone <repo-url>
cd runway
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Frontend

```bash
cd frontend
npm install
```

### Database

Apply migrations to initialize the SQLite database:

```bash
cd backend
alembic upgrade head
```

The database is created at `backend/runway.db`.

## Running Locally

Start both backend and frontend with a single command:

```bash
./run.sh
```

This starts:

- **Backend** at [http://localhost:8000](http://localhost:8000)
- **Frontend** at [http://localhost:5173](http://localhost:5173)

It will also start Ollama automatically if installed.

To run services individually:

```bash
# Backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --port 8000 --reload

# Frontend (in a separate terminal)
cd frontend
npm run dev
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
make backup
```

## Testing

### Backend

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm run test
```

## Available Make/Just Commands

| Command        | Description                              |
| -------------- | ---------------------------------------- |
| `./run.sh`     | Start backend and frontend together      |
| `make backup`  | Create a timestamped database backup     |
| `just migrate` | Apply all pending Alembic migrations     |
| `just dev`     | Run `./run.sh`                           |
| `just backup`  | Create a timestamped database backup     |

## Docker

### Quick Start

Build and run Runway with Docker Compose:

```bash
cp .env.example .env
docker compose up
```

The app will be available at [http://localhost:8000](http://localhost:8000). Migrations run automatically on startup.

### Using an Existing Database

To use an existing `runway.db`, copy it into the container's data volume:

```bash
# Start once to create the volume
docker compose up -d
# Copy your database into the running container
docker cp /path/to/your/runway.db $(docker compose ps -q app):/app/data/runway.db
# Restart to run migrations
docker compose restart
```

Alternatively, switch to a bind mount in `docker-compose.yml` to use a local directory:

```yaml
volumes:
  - ./data:/app/data
```

Then place your `runway.db` in the `./data/` directory before starting.

### AI Features (Optional)

Runway uses LLM-powered parsing for job postings. Without an LLM, it falls back to heuristics.

**Ollama (local, free):** If [Ollama](https://ollama.com) is running on your host machine, the Docker container connects to it automatically — no configuration needed.

**Cloud LLM provider:** Set your provider's API key in `.env`:

```bash
# OpenAI
AI_MODEL=gpt-4o
OPENAI_API_KEY=sk-...

# Or Anthropic
AI_MODEL=anthropic/claude-sonnet-4-20250514
ANTHROPIC_API_KEY=sk-ant-...
```

### Environment Variables

Configuration is done via environment variables. Copy `.env.example` to `.env` and adjust as needed:

| Variable         | Description                              | Default                          |
| ---------------- | ---------------------------------------- | -------------------------------- |
| `DATABASE_PATH`  | Path to the SQLite database file         | `/app/data/runway.db` (Docker)   |
| `CORS_ORIGINS`   | Comma-separated list of allowed origins  | `http://localhost:8000`          |
| `STATIC_DIR`     | Path to built frontend static files      | `/app/frontend/build` (Docker)   |
| `OLLAMA_BASE_URL`| URL of the Ollama server                 | `http://localhost:11434`         |
| `AI_MODEL`       | LLM model to use for parsing             | Ollama default                   |

## Key Dependencies

### Backend

| Package        | Purpose                    |
| -------------- | -------------------------- |
| fastapi        | Web framework              |
| uvicorn        | ASGI server                |
| sqlalchemy     | ORM                        |
| alembic        | Database migrations        |
| pydantic       | Data validation            |
| python-jobspy  | Job board scraping         |
| litellm        | LLM integration            |
| httpx          | HTTP client                |
| beautifulsoup4 | HTML parsing               |
| apscheduler    | Background task scheduling |

### Frontend

| Package              | Purpose                  |
| -------------------- | ------------------------ |
| @sveltejs/kit        | Application framework    |
| svelte               | UI framework             |
| typescript           | Type checking            |
| vite                 | Build tool               |
| marked               | Markdown rendering       |
| dompurify            | HTML sanitization        |
| @sveltejs/adapter-static | Static site generation |
