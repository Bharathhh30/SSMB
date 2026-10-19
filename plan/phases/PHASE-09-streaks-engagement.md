# Phase 9 — Streaks and engagement

**Status:** Not started
**Goal:** Add optional, user-controlled engagement features without manipulative defaults.

## Backend-first sequencing

Implement the activity ledger, deterministic calculations, and reminder
preferences before adding streak or engagement UI.

## Backend work

- Define what counts as meaningful activity, timezone boundary, grace periods, pauses, corrections, and account/community eligibility.
- Derive streaks from an auditable activity ledger; make aggregate snapshots rebuildable.
- Define minimal product analytics and retention with privacy review before instrumentation.
- Test timezone changes, daylight-saving boundaries, delayed and duplicate
  activity events, paused/disabled users, and rebuild consistency.

## Deferred frontend work

Streak/history, reminder, quiet-hour, and privacy controls wait until the
Backend Completion Gate.

## Exit criteria

- Timezone changes, travel, daylight-saving, delayed events, and duplicate events produce deterministic results.
- Streak participation and related notifications can be disabled without impairing core community use.
