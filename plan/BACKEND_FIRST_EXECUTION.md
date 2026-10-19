# Backend-first execution and API verification plan

**Status:** Active
**Last updated:** 2026-10-19
**Authority:** This document operationalizes the cumulative scope in `ROADMAP.md`.

## 1. Sequencing decision

The mobile application has become a source of iteration friction. From this
point, implementation is backend-first:

1. Freeze mobile screen, navigation, dependency, and styling work. Preserve the
   current local prototype; do not extend or delete it during this track.
2. Complete each domain API, its PostgreSQL model/migration, business rules,
   authorization, and automated endpoint/edge-case tests before starting the
   next domain.
3. Reach the **Backend Completion Gate** below. Only then resume frontend
   feature work and integrate it against the tested API contracts.
4. Keep hosting, public domains, store delivery, and production deployment last,
   as already agreed.

This changes implementation order, not product scope. Communities, identity,
profiles, files, messages, notifications, events, reservations, moderation,
voice, and engagement remain included.

## 2. Backend implementation order

| Order | Existing plan phase | Backend deliverables | Current state |
|---:|---|---|---|
| 0 | Product decisions | Resolve only decisions needed before each affected API; define endpoint and permission contracts | Open; keep unresolved decisions explicit |
| 1 | Engineering foundation | FastAPI, PostgreSQL, Alembic, local test database, health/readiness, API conventions, stable errors/logging | Foundation exists; endpoint edge coverage and repeatable DB test setup need work |
| 2 | Identity and profile | Registration/sign-in method, verification/recovery, sessions, profile, preferences, account controls | Not implemented; auth method and age/audience decisions remain open |
| 3 | Communities and discovery | Create/read/update/archive, join/leave/requests, invites, memberships, roles, ownership, access rules | Public read-only discovery exists; write and membership APIs are absent |
| 4 | Content and files | Posts, links, saved items, file metadata, upload/download authorization and storage adapter | Not implemented; storage and retention decisions remain open |
| 5 | Messaging and notifications | Conversations, messages, read cursors, notification inbox/outbox, delivery adapters | Not implemented; realtime and push decisions remain open |
| 6 | Scheduling and reservations | Events, RSVP, resource availability/reservation, reminder scheduling | Not implemented; reservation semantics remain open |
| 7 | Moderation and safety | Reports, queues, actions, appeals, escalation, audit records | Not implemented; policy and staffing decisions remain open |
| 8 | Voice rooms | Server authorization and provider-neutral session/credential boundary | Not implemented; voice provider and consent policies remain open |
| 9 | Streaks and engagement | Activity ledger, derived streaks, user-controlled reminder preferences | Not implemented; activity and timezone rules remain open |

Each phase document remains the detailed scope checklist. Mobile/API integration
work listed there is deferred until after the Backend Completion Gate.

## 3. Endpoint test contract

For every endpoint, write down its actor, authorization rule, request/response
schema, persistence effects, status codes, and observable failure behavior. Add
tests for every applicable case below; mark a case not applicable with a
reason rather than silently omitting it.

### Request and response boundaries

- Valid minimum, typical, and maximum accepted values.
- Missing required fields, explicit `null`, empty strings, whitespace-only
  strings, malformed UUIDs/URLs/timestamps, invalid enums, extra fields, and
  over-limit payloads.
- Pagination lower/upper bounds, beyond-end offsets, stable ordering, and
  filter/search normalization.
- Response-model allowlisting: no credentials, private fields, internal IDs,
  signed URLs, or cross-tenant data leak.

### Identity, authorization, and abuse

- Anonymous, authenticated, wrong-role, suspended/blocked, and authorized
  callers as applicable.
- Owner/member/moderator/operator permission matrix for each protected action.
- Cross-user and cross-community IDOR attempts, including guessed IDs/slugs.
- Duplicate, replayed, expired, revoked, throttled, and concurrent requests;
  idempotency behavior where actions can be retried.

### Persistence and failure handling

- Database constraints and foreign keys, transaction rollback, uniqueness
  collisions, deletion/expiry boundaries, and concurrent write races.
- Database unavailable/timeout and dependency/provider failure behavior.
- Migration upgrade from the previous revision; downgrade/restore behavior where
  safe and meaningful.
- Request IDs on failures; logs exclude secrets, tokens, message bodies, and
  private URLs.

## 4. Existing API surface under hardening

| Endpoint | Current contract | Edge cases to verify |
|---|---|---|
| `GET /api/v1/health` | Process liveness, does not require PostgreSQL | Stable schema/version, request ID, no dependency on DB availability |
| `GET /api/v1/health/ready` | Database readiness; unavailable/unconfigured DB returns 503 | DB absent, connection failure, successful `SELECT 1`, safe response/logging |
| `GET /api/v1/communities` | Open and unexpired communities only; bounded pagination; `q` partial case-insensitive, `topic` exact after trim | Input bounds, blank normalization, wildcard escaping, active/expired/private filtering, stable order, beyond-end offset |
| `GET /api/v1/communities/{slug}` | Public preview only; private, expired, and unknown slugs are indistinguishable 404s | Slug alphabet/length, expiry boundary, private metadata non-disclosure, response field allowlist |
| `GET /api/v1/topics` | Distinct trimmed topics with active open communities; capped at 50 | Exclude private/expired, trim/dedupe, ordering, cap, DB unavailable |

This is only the currently implemented public surface. Each new feature phase
must add its endpoint inventory and test matrix before its API is considered
complete.

## 5. Required test layers and completion evidence

1. **Unit tests:** pure domain rules and services, including edge values.
2. **API contract tests:** FastAPI ASGI requests assert status, response body,
   headers, validation failures, and authorization outcomes.
3. **PostgreSQL integration tests:** run against a disposable database migrated
   by Alembic; exercise real constraints, query semantics, transactions, and
   concurrency-sensitive rules.
4. **Migration checks:** upgrade from the previous head and inspect generated
   upgrade/downgrade SQL; never use ORM `create_all` as a migration substitute.
5. **OpenAPI checks:** verify every implemented endpoint is versioned,
   documented, and has the intended request/response/error schema.
6. **CI:** run backend formatting, lint, unit/API tests, and PostgreSQL-backed
   migration/integration tests independently of mobile checks.

### Backend Completion Gate

Do not resume frontend feature implementation until all of the following are
true:

- Every planned backend domain has an implemented or explicitly decision-gated
  API contract; no capability is silently dropped.
- Each implemented endpoint has the applicable request, authorization,
  persistence, concurrency/idempotency, and failure tests above.
- The complete backend suite runs with **zero skipped database integration
  tests** in the designated disposable PostgreSQL CI/test environment.
- Alembic upgrades cleanly from the previous revision; migrations have been
  reviewed and tested against PostgreSQL.
- OpenAPI is the reviewed integration contract and contains no accidental
  internal/private fields.
- No unresolved critical/high backend security findings remain; remaining
  provider or policy decisions are explicit release blockers, not fake
  integrations.

## 6. Baseline evidence and immediate next steps

At the start of the backend-first pivot, local backend checks reported:

- `uv run --locked pytest`: 21 passed, 1 skipped. The skipped test is the
  PostgreSQL repository integration test because `TEST_DATABASE_URL` was not
  configured for that run.
- `uv run --locked ruff check .`: passed.
- `uv run --locked ruff format --check .`: passed.
- The local Compose PostgreSQL service was observed healthy on 2026-10-19, but
  its persistent developer database is not automatically a disposable test
  database and must not be used as one without an explicit isolation plan.
- The first edge-case test slice added bounds, blank-filter normalization, and
  invalid/max-length slug coverage. A later run must record the exact new
  passing count and the still-skipped PostgreSQL test.

Immediate execution:

1. [x] Expand boundary and failure tests for community discovery, public
   preview slug validation, and health readiness.
2. [x] Verify the full suite and initial Alembic migration on a fresh temporary
   PostgreSQL 18 cluster; enforce DB-test presence in CI.
3. [ ] Continue hardening all current public endpoint behavior, then implement
   new backend domains in the order above with Alembic revisions and tests in
   each reviewable commit.
4. [x] Keep frontend files untouched during this backend-first slice.

### Verified after the first hardening slice

- `uv run --locked pytest -p no:cacheprovider` against a fresh, isolated
  PostgreSQL 18 cluster: **39 passed, 0 skipped** after applying Alembic.
- Without `TEST_DATABASE_URL`, local unit/API checks: **37 passed, 2 expected
  database-test skips**. In CI, the missing URL causes those tests to run and
  fail rather than silently skip.
- `uv run --locked ruff check .` and `uv run --locked ruff format --check .`:
  passed.
- Added tests cover query min/max bounds and malformed values, empty-filter
  normalization, slug syntax/length, readiness success/failure, case-insensitive
  name/description search, literal SQL wildcard search, private/expired row
  exclusion, duplicate-trimmed topics, stable equal-name ordering, and
  beyond-end pagination.
- The temporary test cluster was stopped and removed. The persistent Compose
  database was not changed.

## 7. Deferred frontend integration

After the Backend Completion Gate, resume the existing Expo prototype in
vertical slices. Generate or review typed API contracts, connect one complete
user journey at a time, and test loading, empty, error, offline,
permission-denied, and retry behavior against the real local API. The frontend
is a client of the API; it never connects directly to PostgreSQL.
