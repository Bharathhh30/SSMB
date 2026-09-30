# Phase 8 — Voice rooms

**Status:** Not started
**Goal:** Add cross-platform live audio without building custom media infrastructure prematurely.

## Work

- Compare managed voice providers for mobile SDK maturity, global regions, moderation tools, privacy/recording policy, pricing, capacity, and migration path.
- Implement server-authorized room/session creation and short-lived join credentials; do not expose provider secrets in the app.
- Add lobby, device/permission checks, join/leave, mute/deafen, participant state, host/moderator controls, reconnect, and graceful failure.
- Integrate voice rooms with scheduled sessions and reservation rules without coupling provider-specific IDs to core domain models.
- Define room safety/reporting, recording/consent, blocking, capacity, quality monitoring, and abuse response.

## Exit criteria

- iOS/Android device QA covers permissions, audio route changes, background/foreground, poor network, reconnect, and host moderation.
- Provider cost/capacity limits and user-facing privacy/recording policies are approved.
