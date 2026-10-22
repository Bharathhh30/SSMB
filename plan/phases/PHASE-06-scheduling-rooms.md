# Phase 6 — Events, room reservations, and reminders

**Status:** Not started
**Goal:** Help groups coordinate sessions and reserve the agreed room/resource types.

## Backend-first sequencing

Implement scheduling, reservation, and reminder APIs with transaction-safe
invariants before any calendar or room UI work.

## Backend work

- Define event/session, time zone, recurrence (if required), capacity, RSVP, cancellation, and notify-me semantics.
- Implement resource availability and reservation conflict detection with transactional/constraint protection and idempotent retries.
- Add scheduled reminder jobs, delivery retries, cancellation/reschedule reconciliation, and user quiet hours.
- Confirm whether “room reservation” includes a physical resource, virtual room, or both; keep resource booking separate from voice-session lifecycle.
- Test timezone and daylight-saving boundaries, invalid/past times, capacity,
  overlapping concurrent reservations, duplicate RSVP/cancel, reschedule, and
  stale reminder suppression.

## Deferred frontend work

Calendar, RSVP, availability, reservation, and reminder screens wait until the
Backend Completion Gate.

## Exit criteria

- Time zones and daylight-saving transitions are handled predictably.
- Concurrent reservations cannot double-book the same constrained resource.
- Reminder delivery is retry-safe; canceled or rescheduled events do not send stale reminders.
