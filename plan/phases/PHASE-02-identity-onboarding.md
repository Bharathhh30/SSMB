# Phase 2 — Identity, onboarding, and profile APIs

**Status:** Backend work not started — authentication and audience decisions
remain open; existing mobile mocks are frozen.
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

## Decisions required before affected endpoints

- Select the authentication method, verification/recovery flow, session/token
  policy, and required email/SMS delivery adapters. The existing email/password
  screens are UI mocks only, not an approved design.
- Confirm initial audience/age requirements, profile fields, interest taxonomy,
  profile visibility, and account deletion/export rules.

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
