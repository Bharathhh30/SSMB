# Phase 1 — Backend engineering foundation

**Status:** In progress — local backend exists; endpoint edge coverage and a
repeatable disposable PostgreSQL test workflow are the active tasks.
**Goal:** Make the FastAPI/PostgreSQL backend safe to extend and easy to test.

## Implementation order

Backend/API work only. The Expo app and its existing local screens are preserved
but frozen; no frontend feature or dependency work is scheduled until the
Backend Completion Gate in `../BACKEND_FIRST_EXECUTION.md` passes.

## Backend scope

- Keep the FastAPI API versioned under `/api/v1` and organized as a modular
  monolith with routes, schemas, services, repositories, and models separated.
- Keep PostgreSQL schema changes in reviewed Alembic revisions.
- Provide local startup, readiness, deterministic development seed, and
  disposable PostgreSQL integration-test instructions.
- Expand edge-case coverage for health/readiness, public community discovery,
  topic listing, and public preview before starting new feature endpoints.
- Standardize validation/error shapes, request IDs, redacted logs, pagination,
  and OpenAPI contracts.
- Run backend format, lint, unit/API tests, migration checks, and
  PostgreSQL-backed integration tests independently of mobile CI.

## Deferred

- New Expo screens, frontend navigation/dependencies, and mobile API wiring.
- Hosting, custom domains, paid cloud resources, and production environments.
- Branch protections and deployment automation until production choices are
  approved.

## Existing foundation

- [x] FastAPI liveness and database-readiness endpoints.
- [x] Async SQLAlchemy/PostgreSQL configuration and initial users/communities
  Alembic revision.
- [x] Public open-community list, topic list, and public-preview endpoints.
- [x] Request IDs and redacted structured HTTP logs.
- [x] Explicit development seed command guarded by `APP_ENV=development`.
- [x] Backend formatting and lint checks pass.
- [x] Expand current endpoint boundary and failure-case tests for community
  discovery and slug validation.
- [x] Run the full suite against a fresh PostgreSQL 18 temporary cluster after
  applying Alembic; the full run passed without skipped tests.
- [x] Ensure PostgreSQL-backed tests cannot be skipped in CI when
  `TEST_DATABASE_URL` is missing.

## Exit criteria

- Clean setup starts a local API and PostgreSQL database, applies Alembic
  migrations, and seeds development data using documented commands.
- The backend unit/API suite and database-backed integration suite are
  repeatable; no DB-backed tests are silently skipped in the designated CI
  environment.
- Existing public endpoints have documented contracts and edge-case tests.
- Migration, lint, and format checks pass.
