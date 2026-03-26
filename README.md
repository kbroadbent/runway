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
