# Backend-first execution and API verification plan

**Status:** Active
**Last updated:** 2026-10-22
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
| 2 | Identity and profile | Registration/sign-in, verification/recovery, sessions, profile, preferences, account controls | Auth and private self-profile endpoints implemented/tested; privacy, block, deletion/export APIs remain |
| 3 | Communities and discovery | Create/read/update/archive, join/leave/requests, invites, memberships, roles, ownership, access rules | Discovery, create/manage, join/leave, single-use invites, owner/self-membership lists, owner/moderator roster reads, audited moderator assignment/removal, and audited ownership transfer are PostgreSQL-tested; archive semantics remain |
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
| `GET /api/v1/communities` | Open and unexpired communities only; bounded pagination; returns public IDs, never DB primary keys | Input bounds, blank normalization, wildcard escaping, active/expired/private filtering, stable order, beyond-end offset, response identifier allowlist |
| `GET /api/v1/communities/{slug}` | Public preview with `public_id` and current `member_count`; private, expired, and unknown slugs are indistinguishable 404s | Slug alphabet/length, expiry boundary, exact membership count, private metadata non-disclosure, no internal ID leak |
| `GET /api/v1/topics` | Distinct trimmed topics with active open communities; capped at 50 | Exclude private/expired, trim/dedupe, ordering, cap, DB unavailable |
| `POST /api/v1/communities` | Verified signed-in user creates an `open` or `invite_only` community; creator receives owner membership; new slug is normalized name plus full public UUID | Anonymous/revoked session, invalid/blank/oversized fields, timezone-less/past expiry, extra fields, case/whitespace duplicate names, unique public slug, internal-ID non-disclosure, transaction atomicity, response allowlist |
| `POST /api/v1/communities` | Verified signed-in user creates an `open` or `invite_only` community; returns public ID and name-plus-public-ID slug | Anonymous/revoked session, invalid/blank/oversized fields, timezone-less/past expiry, extra fields, case/whitespace duplicate names, internal-ID non-disclosure, transaction atomicity |
| `POST /api/v1/communities/{slug}/join` | Authenticated user joins an active open community; retries return membership identified by `community_slug` | Anonymous, invalid/unknown/private/expired slug, duplicate/concurrent joins, unique membership constraint, no internal ID leak |
| `DELETE /api/v1/communities/{slug}/leave` | Authenticated member leaves; repeated leave from an active open community is idempotent; owner must transfer ownership first | Anonymous, unknown/private non-member, expired community, owner denial, repeated/concurrent leave, transaction consistency |
| `POST /api/v1/communities/{slug}/invites` | Owner creates a single-use invite for an invite-only community; raw token is returned once and expires within seven days | Anonymous/non-owner, open/expired community, duplicate requests, hash-only persistence, expiry boundary, throttling |
| `GET /api/v1/communities/{slug}/invites` | Owner reads paginated invite metadata and lifecycle status; never returns invite tokens | Anonymous/non-owner, unknown slug, pagination boundaries, active/accepted/revoked/expired status |
| `DELETE /api/v1/communities/{slug}/invites/{invite_public_id}` | Owner revokes an unused invite by public identifier; repeated revoke is idempotent | Anonymous/non-owner, cross-community invite ID, unknown invite, accepted invite conflict, concurrent acceptance/revoke |
| `POST /api/v1/communities/invites/accept` | Verified signed-in user accepts a token; same-user retries are idempotent | Anonymous/unverified, invalid/expired/revoked, replay by another user, concurrent acceptance, existing membership, throttling |
| `GET /api/v1/communities/mine` | Authenticated user lists owned communities, including invite-only/expired entries; responses use public identifiers only | Anonymous, pagination bounds/order, no cross-owner rows or internal IDs |
| `GET /api/v1/communities/{slug}/manage` | Community owner reads their community, including invite-only or expired records; non-owner gets 403 and unknown slug gets 404 | Anonymous, unknown slug, cross-owner status/message, owner/private-field response allowlist |
| `PATCH /api/v1/communities/{slug}` | Owner updates name, topic, description, access type, or expiry; slug remains stable; non-owner gets 403 and unknown slug gets 404 | Anonymous, non-owner/member status/message, blank/null/oversized fields, empty patch, extra fields, invalid expiry, explicit expiry clear, concurrent writes |
| `GET /api/v1/communities/memberships/me` | Authenticated caller lists their own current membership records, including owned communities; returns public community data and role | Anonymous, bounded pagination, ordering, expired-community status, no arbitrary user lookup or internal ID leakage |
| `GET /api/v1/communities/{slug}/members` | Community owner or moderator lists the current roster; returns user public IDs, display names, roles, and join times only | Anonymous/member/unrelated owner denial, unknown slug, private/expired owner access, cross-community isolation, pagination, no email/internal ID leakage |
| `PUT /api/v1/communities/{slug}/members/{user_public_id}/role` | Owner sets an existing member to `moderator` or `member`; actual changes are transactionally audited and retries are idempotent | Anonymous/non-owner, owner-target conflict, unknown/cross-community target, invalid/extra fields, concurrent writes, exactly one event for a concurrent repeated change, audit response/DB allowlist |
| `POST /api/v1/communities/{slug}/transfer-ownership` | Current owner transfers to an existing community member; target becomes owner and former owner becomes member; mutation is atomic and audited | Anonymous/non-owner, self/non-member/cross-community target, malformed/extra fields, concurrent transfer, exactly one owner membership, post-transfer owner/leave permissions, audit response/DB allowlist |
| `GET /api/v1/profile/me` | Authenticated caller's public ID, display name, and private interests | Missing/expired/revoked auth, no internal ID/email/hash leakage, empty interests |
| `PATCH /api/v1/profile/me` | Update caller's display name; add/remove private interests | Blank/null/unknown/oversized/duplicate values, atomic add/remove behavior, clearing interests |

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

### Identity decision, API implementation, and verification

- The owner approved email/password authentication, mandatory email
  verification, account recovery, and deferring social sign-in. See
  `../docs/decisions/0002-email-password-authentication.md`.
- Current identity routes:

  | Method / route | Purpose | Expected boundary outcomes |
  |---|---|---|
  | `POST /api/v1/auth/register` | Create an unverified account and send verification | `202` generic response; schema errors `422`; throttled `429` |
  | `POST /api/v1/auth/verification/resend` | Reissue verification email | `202` generic response for known/unknown; throttled `429` |
  | `POST /api/v1/auth/verify-email` | Consume one-time verification token | `200`; invalid/expired/replayed token `400`; throttled `429` |
  | `POST /api/v1/auth/login` | Create access/refresh session for verified account | `200`; generic bad/unverified credentials `401`; throttled `429` |
  | `GET /api/v1/auth/me` | Read allowlisted current-user fields | `200`; missing/expired/revoked access token `401` |
  | `POST /api/v1/auth/refresh` | Rotate refresh token and access session | `200`; invalid/expired/replayed token `401`; replay revokes session |
  | `POST /api/v1/auth/logout` | Revoke current session | `204`; unauthenticated `401` |
  | `POST /api/v1/auth/password/forgot` | Request recovery instructions | `202` generic response for known/unknown; throttled `429` |
  | `POST /api/v1/auth/password/reset` | Consume recovery token and revoke sessions | `200`; invalid/expired/replayed token `400`; invalid password `422` |
  | `GET /api/v1/profile/me` | Read caller's private profile | `200`; unauthenticated/expired/revoked session `401` |
| `PATCH /api/v1/profile/me` | Update caller's display name and add/remove private interests | `200`; invalid/duplicate/oversized/unknown fields `422`; unauthenticated `401` |
- Identity migrations add nullable-compatible user email/password hash/
  verification fields, session/refresh/action-token records, and rate-limit
  buckets.
- The identity/profile APIs cover registration, verification/resend, sign-in,
  `/me`, refresh rotation/replay revocation, logout, forgot/reset-password, and
  self-only profile display-name/interest updates.
- Argon2id hashing, normalized email, one-time token hashing, and password
  boundaries have unit tests. PostgreSQL integration covers the full auth
  journey, expiry/replay cases, and login throttling.
- The full suite passed **55/55** against a fresh migrated PostgreSQL 18
  cluster; Alembic model-drift checks passed. The copy/paste local test flow
  passed against the temporary API and Mailpit SMTP catcher.
- Durable email retries/outbox, scheduled/monitored rate-bucket cleanup,
  profile privacy/block/account-control APIs, production SMTP configuration,
  and a separately managed `AUTH_RATE_LIMIT_SECRET` remain outstanding. The cleanup command is
  `python -m app.scripts.prune_auth_rate_limits`; it still needs a scheduled,
  monitored deployment job.

## 7. Deferred frontend integration

After the Backend Completion Gate, resume the existing Expo prototype in
vertical slices. Generate or review typed API contracts, connect one complete
user journey at a time, and test loading, empty, error, offline,
permission-denied, and retry behavior against the real local API. The frontend
is a client of the API; it never connects directly to PostgreSQL.

## 8. Community membership contract hardening (2026-10-22)

- PostgreSQL integration coverage now verifies that
  `GET /api/v1/communities/memberships/me` returns only the authenticated
  caller's memberships, including owner and member roles and memberships for
  expired communities.
- Coverage also verifies active/expired status, page totals, non-overlapping
  pages that account for the full result set, and omission of internal
  membership/community IDs.
- Alembic `upgrade head` and the complete backend suite passed against a fresh,
  isolated PostgreSQL 18 container: **101 passed, 0 skipped**. The container
  had no persistent volume and was removed after the run; the developer's
  local Compose database was not used or modified.

## 9. Community roster contract (October 22, 2026)

- **Approved privacy rule:** only a community owner or moderator may view that
  community's member identities. Public previews continue to expose the
  aggregate member count, and no endpoint reveals all communities another
  person belongs to.
- `GET /api/v1/communities/{slug}/members` is paginated and limited to
  `user_public_id`, `display_name`, `role`, and `joined_at`. It is available for
  invite-only and expired communities to authorized community managers.
- Owner/moderator access, member and cross-community denials, unknown-community
  behavior, pagination, and response allowlisting passed the isolated
  PostgreSQL 18 integration suite. Full suite: **102 passed, 0 skipped**.
- No schema migration was needed for the roster endpoint. Moderator role
  assignment/removal was implemented in the following slice; ownership
  transfer remains separate work.

## 10. Community moderator role management (October 22, 2026)

- Only the community owner may promote an existing member to moderator or
  demote a moderator to member. Moderators cannot manage roles; owner changes
  are reserved for the ownership-transfer operation. Setting a member's
  current role again is an idempotent no-op.
- `PUT /api/v1/communities/{slug}/members/{user_public_id}/role` identifies
  targets by public UUID and only searches within the requested community.
  Non-member and cross-community targets are indistinguishable `404`s. Owner
  targets receive `409`; non-owners receive `403`.
- Alembic `0009_community_role_audit` adds constrained role-change history.
  Membership updates and audit inserts commit in one transaction. No-op
  retries do not create events. Audit events contain public-ID snapshots;
  retention/anonymization must be decided before account/community deletion
  or production launch. Downgrading this revision drops its audit history.
- The migration's generated PostgreSQL SQL was reviewed. Upgrade, downgrade
  to `0008`, re-upgrade, and Alembic drift checks passed on isolated
  PostgreSQL 18. Full suite: **104 passed, 0 skipped**.

## 11. Community ownership transfer (October 22, 2026)

- Only the current owner can transfer ownership, and the target must already
  be a member of the same community. The new owner receives the `owner` role;
  the former owner becomes a regular member. A moderator target does not keep
  moderator status after becoming owner.
- The community owner ID and both membership roles change in one transaction
  after locking the community and affected memberships. A PostgreSQL partial
  unique index prevents more than one owner membership per community. The
  former owner may leave afterward; the new owner cannot leave until another
  transfer.
- `POST /api/v1/communities/{slug}/transfer-ownership` accepts
  `{"new_owner_public_id": "<existing member public UUID>"}`. The target lookup
  is scoped to that community. Non-member/cross-community targets return
  `404`; non-owners receive `403`; self-transfer and inconsistent owner state
  return `409`.
- Alembic `0010_ownership_transfer` creates `community_ownership_changes` and
  the single-owner index. Generated PostgreSQL SQL was reviewed; the migration
  refuses to apply if it finds duplicate owner memberships. Downgrade removes
  ownership history and the index. Audit snapshots still need
  retention/anonymization rules before production account/community deletion.
- The full suite passed **105 tests, 0 skipped** on isolated PostgreSQL 18.
  Upgrade, drift check, downgrade to `0009`, re-upgrade, and a second drift
  check passed. Ruff lint and formatting checks passed.
