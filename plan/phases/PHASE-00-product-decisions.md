# Phase 0 — Product decisions and interface contracts

**Status:** Not started
**Source of truth:** `../ROADMAP.md`
**Goal:** Turn the community concept into a testable product and architecture baseline before implementation.

**Sequencing note:** Backend implementation now precedes frontend implementation.
Resolve decisions incrementally at the affected backend phase gate; do not
block decision-independent backend work, and do not start new mobile work before
the Backend Completion Gate.

## Work

- Validate only the product assumptions needed for the local prototype; defer final brand, public domain, and app-store identifiers until the prototype is approved.
- Confirm the initial audience/language and measurable first-release outcomes before identity, privacy, or public launch features are implemented.
- Turn the screen/interface inventory into user flows and low-fidelity wireframes for iOS and Android, including accessibility and failure states.
- Define the permission matrix for visitor, member, moderator, founder, and platform operator.
- Write API conventions, initial OpenAPI resource schemas, pagination/error/idempotency patterns, and version compatibility policy.
- Define endpoint-level edge-case and authorization test expectations; keep OpenAPI as the eventual frontend integration contract.
- Define initial PostgreSQL domain boundaries, retention/deletion/export rules, and the migration review process.
- Defer cloud host/region/budget and EAS/store setup until after prototype signoff. Evaluate auth, email, notifications, realtime, voice, and monitoring only before their implementation phases.
- Define community privacy defaults, invite/access behavior, content policy, report evidence handling, five-report escalation semantics, appeals, and moderation staffing assumptions.
- Confirm room-reservation semantics: virtual voice room, physical/other scheduled resource, or both.
- Record architecture decisions in `docs/decisions/` as concise ADRs.

## Deliverables

- Approved personas, core journeys, scope boundaries, and non-functional requirements.
- Wireframes or annotated flow diagrams for onboarding, discovery/join, community participation, reports, and scheduling.
- Permission matrix and endpoint/API contract draft.
- Initial entity relationship sketch and data classification/retention table.
- Provider comparison and decision records before deployment, with ownership, cost assumptions, and exit path.
- Risk register and measurable Phase 1 acceptance checks.

## Exit criteria

- Decisions needed for local Phase 1 are resolved; later-phase decisions have an owner/phase and do not pull deployment work into the prototype.
- The Phase 2–10 full scope remains represented; deferrals have a named phase, not an accidental omission.
- Product, API, data, security, and release decisions are coherent and reviewed.
