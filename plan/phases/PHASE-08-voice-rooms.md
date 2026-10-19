# Phase 8 — Voice rooms

**Status:** Not started
**Goal:** Add cross-platform live audio without building custom media infrastructure prematurely.

## Backend-first sequencing

Resolve provider and safety decisions at this phase gate, then implement and
test the server-side authorization and provider boundary before client voice
work.

## Backend work

- Compare managed voice providers for mobile SDK maturity, global regions, moderation tools, privacy/recording policy, pricing, capacity, and migration path.
- Implement server-authorized room/session creation and short-lived join credentials; do not expose provider secrets in the app.
- Integrate voice rooms with scheduled sessions and reservation rules without coupling provider-specific IDs to core domain models.
- Define room safety/reporting, recording/consent, blocking, capacity, quality monitoring, and abuse response.
- Test unauthorized/expired join credentials, room capacity, role controls,
  provider timeouts, retries, leave/revoke behavior, and policy-denied access.

## Deferred frontend work

Lobby, device permissions, join/leave, audio controls, participant state, and
reconnect UI wait until the Backend Completion Gate and a selected voice
provider.

## Exit criteria

- iOS/Android device QA covers permissions, audio route changes, background/foreground, poor network, reconnect, and host moderation.
- Provider cost/capacity limits and user-facing privacy/recording policies are approved.
