# Phase 2 — Identity, onboarding, and profile

**Status:** Not started
**Goal:** Deliver secure account creation and a useful member profile foundation.

## Work

- Implement the selected authentication and verification/recovery methods.
- Add token/session lifecycle, refresh/revocation, secure mobile storage, logout, session-expired recovery, and abuse throttling.
- Implement profile read/update, topics/interests, privacy preferences, block controls, and account deletion/export entry points.
- Build welcome, registration/login, verification, recovery, profile, and security/settings screens.
- Add server-side authorization, redacted structured audit/security events, and privacy/legal consent capture as required.

## Exit criteria

- Signup/login/recovery/logout/session-expiry work on iOS and Android.
- Negative tests cover invalid credentials, expired/replayed refresh, unauthorized profile access, and rate limits.
- Account data is never exposed through client bundles or logs; deletion/export behavior is documented.
