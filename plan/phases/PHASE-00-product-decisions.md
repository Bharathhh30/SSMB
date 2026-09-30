# Phase 0 — Product decisions and interface contracts

**Status:** Not started
**Source of truth:** `../ROADMAP.md`
**Goal:** Turn the community concept into a testable product and architecture baseline before implementation.

## Work

- Validate launch audience, initial region/language, age policy, product name, and measurable first-release outcomes.
- Turn the screen/interface inventory into user flows and low-fidelity wireframes for iOS and Android, including accessibility and failure states.
- Define the permission matrix for visitor, member, moderator, founder, and platform operator.
- Write API conventions, initial OpenAPI resource schemas, pagination/error/idempotency patterns, and version compatibility policy.
- Define initial PostgreSQL domain boundaries, retention/deletion/export rules, and the migration review process.
- Evaluate cloud/region/database/storage, authentication, email, notifications, real-time messaging, voice, monitoring, and CI provider options; record decisions and costs without locking into unnecessary services.
- Define community privacy defaults, invite/access behavior, content policy, report evidence handling, five-report escalation semantics, appeals, and moderation staffing assumptions.
- Confirm room-reservation semantics: virtual voice room, physical/other scheduled resource, or both.
- Record architecture decisions in `docs/decisions/` as concise ADRs.

## Deliverables

- Approved personas, core journeys, scope boundaries, and non-functional requirements.
- Wireframes or annotated flow diagrams for onboarding, discovery/join, community participation, reports, and scheduling.
- Permission matrix and endpoint/API contract draft.
- Initial entity relationship sketch and data classification/retention table.
- Provider comparison and decision records with ownership, cost assumptions, and exit path.
- Risk register and measurable Phase 1 acceptance checks.

## Exit criteria

- All decisions that block Phase 1 are resolved or explicitly assigned an owner/date.
- The Phase 2–10 full scope remains represented; deferrals have a named phase, not an accidental omission.
- Product, API, data, security, and release decisions are coherent and reviewed.
