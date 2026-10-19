# Phase 2 — Identity, onboarding, and profile APIs

**Status:** In progress — email/password with verification and recovery approved; backend implementation is beginning. Existing mobile mocks remain frozen.
**Goal:** Implement and exhaustively test identity, session, profile, and
account APIs before resuming their frontend work.

## Backend work

- Implement the selected authentication and verification/recovery methods.
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

- Select an email-delivery adapter before enabling real verification and
  recovery delivery. Use fakes in tests and fail explicitly if delivery is not
  configured; do not log verification or reset tokens.
- Confirm initial audience/age requirements, profile fields, interest taxonomy,
  profile visibility, and account deletion/export rules.

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
- [ ] Review endpoint request/response and abuse contracts before opening
  registration and recovery routes.
- [ ] Implement registration, email verification, sign-in, session refresh and
  revocation, sign-out, and current-user endpoints.
- [ ] Implement rate limits, generic recovery responses, and password reset
  with the replaceable email-delivery adapter.
