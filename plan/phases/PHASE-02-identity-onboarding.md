# Phase 2 — Identity, onboarding, and profile

**Status:** In progress — local UI exploration only; authentication method and provider remain undecided.
**Goal:** Progressively prototype identity/onboarding, then implement secure account access after the owner approves the authentication approach.

## Work

- Prototype the welcome, sign-up, and sign-in screens without transmitting or persisting credentials. Treat email/password as a visual exploration only, not a provider decision.
- Implement the selected authentication and verification/recovery methods.
- Add token/session lifecycle, refresh/revocation, secure mobile storage, logout, session-expired recovery, and abuse throttling.
- Implement profile read/update, topics/interests, privacy preferences, block controls, and account deletion/export entry points.
- Build welcome, registration/login, verification, recovery, profile, and security/settings screens.
- Add server-side authorization, redacted structured audit/security events, and privacy/legal consent capture as required.

## Exit criteria

- Signup/login/recovery/logout/session-expiry work on iOS and Android.
- Negative tests cover invalid credentials, expired/replayed refresh, unauthorized profile access, and rate limits.
- Account data is never exposed through client bundles or logs; deletion/export behavior is documented.

## Local prototype progress

- [x] Add a guest-preserving account entry point from Home with welcome, sign-up, and sign-in screens.
- [x] Add client-side draft validation and clear prototype-only messaging; the forms do not call the API or store credentials.
- [ ] Review the screens on Android and iOS and capture the owner's visual/flow feedback.
- [ ] Decide the authentication method, verification, recovery, and audience/age requirements before implementing a real account flow.

This prototype does not create a user, establish a session, or unlock protected community actions.
