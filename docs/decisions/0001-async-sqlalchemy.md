# ADR 0001: Async SQLAlchemy for the FastAPI/PostgreSQL foundation

- **Status:** Provisional; implemented for Phase 1, production approval pending
- **Date:** 2026-09-30
- **Decision owners:** Product/project owner and engineering

## Context

The project selected FastAPI, PostgreSQL, and Alembic. The API needs an explicit
persistence layer that can serve asynchronous FastAPI routes, keep database
sessions scoped to requests, and expose model metadata to Alembic. The
roadmap's ORM choice remains an open Phase 0 decision, so this implementation
must not be mistaken for an irreversible production-provider commitment.

## Decision

Use SQLAlchemy 2.x's asynchronous engine and session APIs with the `asyncpg`
driver for the current foundation. Use Alembic's asynchronous migration
environment for all schema changes. Create one engine/session factory per API
process and dispose the engine through the FastAPI lifespan; do not create
tables automatically at application startup.

This is a provisional engineering choice so the initial schema and API can be
built and exercised. Revisit the decision before production after comparing
async SQLAlchemy with synchronous SQLAlchemy/psycopg for the team's transaction,
pooling, migration, and operational needs.

## Consequences

- Database calls in request handlers must be awaited and use request-scoped
  `AsyncSession` instances.
- Alembic revisions remain explicit deployment steps; model metadata is used
  for autogeneration, but generated revisions require review.
- PostgreSQL-backed integration tests are required for database behavior;
  mocked API tests alone are insufficient.
- The database URL is secret server configuration and is never bundled into the
  mobile app.
- The managed PostgreSQL provider, region, and deployment target remain open.
