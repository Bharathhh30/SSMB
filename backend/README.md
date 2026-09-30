# Community API

The API is a FastAPI modular monolith. Public endpoints are versioned under
`/api/v1`. This first slice provides a liveness endpoint only; it does not
claim that PostgreSQL or other dependencies are ready yet.

## Local development

From the repository root:

```powershell
Set-Location backend
uv sync --locked
uv run uvicorn app.main:app --reload
```

The liveness endpoint is `http://127.0.0.1:8000/api/v1/health`. Interactive API
docs are available at `http://127.0.0.1:8000/docs` in development only.

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

## Health semantics

`GET /api/v1/health` is a liveness check: it confirms that the API process can
serve requests. It intentionally does not report database readiness. A
readiness check will be added alongside the PostgreSQL connection and migration
foundation, when it can verify those dependencies rather than return a
misleading success.
