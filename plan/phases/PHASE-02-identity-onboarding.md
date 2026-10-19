# Phase 2 — Identity, onboarding, and profile APIs

**Status:** In progress — email/password identity and private self-profile APIs are implemented and integration-tested. Privacy/block/account-control APIs remain; mobile mocks are frozen.
**Goal:** Implement and exhaustively test identity, session, profile, and
account APIs before resuming their frontend work.

## Backend work

- Implement and harden registration, verification, sign-in, session rotation,
  sign-out, recovery, and password reset.
- Add token/session lifecycle, refresh/revocation, secure session handling,
  logout, session-expired behavior, and abuse throttling.
- Implement profile read/update, interests, privacy preferences, block controls,
  and account deletion/export entry points.
- Add server-side authorization, redacted security/audit events, and consent
  capture as required by approved policy.
- Test signup, signin, verification, recovery, refresh, revoke, logout, profile
  access, rate limits, and account controls, including invalid, expired,
  replayed, unauthorized, and cross-user cases.

## Decisions still required before affected endpoints

- Local development uses the replaceable SMTP adapter with Mailpit. Select and
  configure production email delivery before launch; do not log verification or
  reset tokens.
- Staging/production must provide `AUTH_RATE_LIMIT_SECRET` through their secret
  manager.
- Confirm initial audience/age requirements, public profile visibility,
  curated interest taxonomy, privacy preferences, and account deletion/export
  rules. The current private self-profile API intentionally exposes no profile
  to other users.

The approved authentication decision is recorded in
`../../docs/decisions/0002-email-password-authentication.md`.

## Deferred frontend work

The current welcome, sign-up/sign-in, and profile-preview screens remain in the
repository as disposable prototypes. Do not extend or connect them until this
phase's API contracts and tests pass and the Backend Completion Gate opens
frontend work.

## Exit criteria

- Account lifecycle endpoints work with approved verification/recovery policy.
- Negative tests cover invalid credentials, expired/replayed/revoked sessions,
  unauthorized profile access, cross-user access, and throttling.
- Account data is never exposed through response models or logs; deletion/export
  behavior and retention are documented and tested.

## Preserved frontend prototype (frozen; not backend progress)

- [x] Guest-preserving welcome, sign-up, and sign-in screens exist locally.
- [x] Client-side draft validation is local-only and does not contact the API.
- [x] A local profile setup/preview screen demonstrates a display name and
  sample interests without persistence.
- [ ] Review the prototype after the backend completion gate and integrate it
  against the approved identity/profile API.

## Backend implementation progress

- [x] Owner approved email/password registration, required email verification,
  password recovery, and no initial social sign-in.
- [x] Add a backward-compatible identity/session/action-token schema migration.
- [x] Add Argon2id password-hashing, email-normalization, and one-time-token
  primitives with unit tests.
- [x] Review request/response and abuse contracts for account lifecycle routes.
- [x] Implement registration, email verification, sign-in, session refresh and
  revocation, sign-out, and current-user endpoints.
- [x] Implement generic recovery responses, password reset, and database-backed
  rate limits with a replaceable SMTP adapter.
- [x] Verify the auth journey and rate-limit behavior against PostgreSQL; test
  the local SMTP path through Mailpit.
- [x] Verify Alembic drift and run the complete database-backed suite with zero
  skipped tests.
- [x] Add self-only profile read/update endpoints for display name and private
  free-form interests, with transactional persistence and input limits.
- [x] Test unauthenticated access, allowed updates, blank/duplicate/oversized
  values, unknown fields, and interest clearing.
- [x] Document copy/paste payloads and provide a PowerShell smoke script that
  exercises the full local auth journey without Swagger.
- [x] Add a bounded rate-limit bucket cleanup command.
- [ ] Schedule/monitor that cleanup and add durable email retry/outbox behavior
  before production hardening.
- [ ] Implement privacy controls, block controls, and account deletion/export
  endpoints after their policy decisions are approved.
