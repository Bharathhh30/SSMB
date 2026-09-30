# Phase 5 — Messaging and notifications

**Status:** Not started
**Goal:** Enable reliable community conversations and user-controlled notifications.

## Work

- Implement conversation/message persistence, membership-aware history, send/edit/delete policy, unread/read cursors, and abuse controls.
- Choose and implement live delivery (managed real-time service or authenticated FastAPI WebSockets) with reconnect, backoff, ordering, and REST history fallback.
- Add notification outbox/worker, in-app inbox, device-token lifecycle, push delivery adapter, and per-community mute/quiet-hour preferences.
- Add report/block affordances and safe handling of notifications on lock screens.
- Build inbox, conversation, unread, notification center, and preference interfaces.

## Exit criteria

- Message history is authoritative in the API/database; live delivery loss recovers through synchronization.
- Cross-community data access, unauthorized sends, blocked-user behavior, rate limits, and reconnects are tested.
- Users can control push/in-app preferences and revoke device registrations.
