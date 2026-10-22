# Phase 5 — Messaging and notifications

**Status:** Not started
**Goal:** Enable reliable community conversations and user-controlled notifications.

## Backend-first sequencing

Implement and test the authoritative message/notification APIs and delivery
boundaries first. Do not build or extend mobile messaging UI before the Backend
Completion Gate.

## Backend work

- Implement conversation/message persistence, membership-aware history, send/edit/delete policy, unread/read cursors, and abuse controls.
- Choose and implement live delivery (managed real-time service or authenticated FastAPI WebSockets) with reconnect, backoff, ordering, and REST history fallback.
- Add notification outbox/worker, in-app inbox, device-token lifecycle, push delivery adapter, and per-community mute/quiet-hour preferences.
- Enforce the approved block/report rules in service and endpoint authorization;
  notification payloads must not expose private content by default.
- Test access isolation, membership changes, blocked users, duplicate sends,
  message limits, unread cursor boundaries, delivery retries, device-token
  revocation, and quiet-hour/timezone behavior.

## Deferred frontend work

Inbox, conversation, unread, notification-center, and preference screens wait
until the Backend Completion Gate.

## Exit criteria

- Message history is authoritative in the API/database; live delivery loss recovers through synchronization.
- Cross-community data access, unauthorized sends, blocked-user behavior, rate limits, and reconnects are tested.
- Users can control push/in-app preferences and revoke device registrations.
