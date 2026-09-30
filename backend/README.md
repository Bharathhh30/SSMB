# Community API

The API is a FastAPI modular monolith. Public endpoints are versioned under
`/api/v1`. PostgreSQL runs locally in Docker Compose, SQLAlchemy uses its async
PostgreSQL driver, and Alembic is configured for future schema revisions.

## Local development

From the repository root:

```powershell
Set-Location backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv sync --locked
docker compose up -d db
uv run --locked alembic upgrade head
uv run --locked python -m app.scripts.seed_development
uv run uvicorn app.main:app --reload
```

The API liveness endpoint is `http://127.0.0.1:8000/api/v1/health`; database
readiness is `http://127.0.0.1:8000/api/v1/health/ready`. Interactive API docs
are available at `http://127.0.0.1:8000/docs` in development only.

The database port is bound to loopback only. Do not expose PostgreSQL through a
tunnel; expose the API instead. `.env.example` contains local-only development
credentials and must never be reused for staging or production.

The explicit seed command creates five repeatable demo communities and one demo
owner. It refuses to run unless `APP_ENV=development`; no seed data is inserted
automatically when the API starts.

## Database migrations

The initial Alembic revision creates the authentication-independent `users`
identity record and the foundational `communities` table, including ownership,
access-type constraints, expiry, and lookup indexes. Authentication-specific
credentials are intentionally not stored in this schema; the authentication
approach remains a separate product decision.

Alembic's asynchronous environment uses `Base.metadata` and `DATABASE_URL`.
Apply schema changes only through reviewed revisions; do not use ORM auto-create
in application startup. Generate later revisions with:

```powershell
uv run --locked alembic revision --autogenerate -m "describe the schema change"
```

Review the generated upgrade and downgrade operations before applying them.
Production migrations remain a controlled deployment step and must not run
automatically on every API replica.

Run checks with:

```powershell
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

Commit `uv.lock` so local and CI installs use the same dependency versions. The
API reads non-secret settings from the process environment. Copy `.env.example`
to `.env` only for local overrides; never commit `.env` or production
credentials.

## Health and community discovery

`GET /api/v1/health` is a liveness check: it confirms that the API process can
serve requests. `GET /api/v1/health/ready` executes `SELECT 1` and returns 503
if the database is missing or unreachable, so an API process is not reported
ready while its required database is unavailable.

`GET /api/v1/communities` returns a bounded page of unexpired communities and
supports `q`, `topic`, `limit` (maximum 100), and `offset`. Until a separate
public-preview policy is defined, unauthenticated discovery returns only
open-access communities; it does not expose invite-only community metadata.
