# Phase 7 — Moderation and trust/safety operations

**Status:** Not started
**Goal:** Make reporting, review, enforcement, and escalation operationally safe.

## Backend-first sequencing

Implement reporting, review queues, policy actions, auditability, and access
controls in the backend before any moderator or report UI work.

## Backend work

- Implement reports for users/content/communities with structured reason, optional explanation/evidence, abuse controls, and status visibility.
- Build community moderator queue/detail/actions and platform escalation queue with restricted access.
- Implement auditable warnings/removal/mute/suspension/ban actions as approved by policy, with scope, duration, reason, and appeal.
- Treat five valid reports as a configurable escalation signal to human review, never automatic guilt or automatic punitive action.
- Add evidence privacy, retention, reviewer access controls, moderation audit trails, and operational response/runbooks.
- Test duplicate/brigaded reports, evidence privacy, conflicts of interest,
  cross-community authorization, action scope/duration, appeals, and audit
  records. A report threshold is only a human-review escalation signal, never
  automatic proof or automatic punishment.

## Deferred frontend work

Report, queue, action, and appeal screens wait until the Backend Completion
Gate.

## Exit criteria

- Report brigading, duplicate reports, conflicts of interest, unauthorized moderator access, and evidence leakage are tested.
- Human-review ownership, response expectations, emergency handling, and appeal process are documented before public communities open.
