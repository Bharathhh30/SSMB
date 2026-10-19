# Community Platform — Cumulative Product and Engineering Roadmap

**Status:** Implementation in progress
**Last updated:** 2026-10-16
**Product source:** `../Community_Platform_Concept.md`
**Repository guidance:** `../AGENTS.md`

This is the cumulative source of truth for product scope, interfaces, technical direction, delivery, and phase gates. Detailed phase checklists live in `plan/phases/`. Work proceeds in order, but each phase may be split into independently reviewable vertical slices.

## 1. Product direction

Build a mobile-first community platform for people to discover and participate in topic-based groups. The initial concept emphasizes study communities; the agreed product scope includes the full concept: communities, moderation, content/files, messaging, events/room reservations, reminders/notifications, voice, and streaks. These are delivered progressively rather than all at once.

### Product principles

- Safe by default: privacy, consent, moderation, and reporting are designed into the domain model and UI.
- Useful before social: make it easy to find a relevant community, join, coordinate, and share trustworthy material.
- Mobile-first and accessible: both iOS and Android are first-class release targets.
- Reliable under poor connectivity: clear loading/offline/error states, retryable actions, and no misleading success UI.
- Incremental architecture: begin with a modular monolith and managed services; add complexity only for a measured need.

### Initial personas

1. **Member/learner:** discovers groups, joins, participates, shares materials, and attends sessions.
2. **Founder:** creates a community, configures access, invites people, and manages moderators.
3. **Moderator:** reviews reports, applies policy actions, and helps keep a community safe.
4. **Platform operator:** handles escalations, abuse, account/security issues, and service health.

These personas are planning assumptions based on the concept document; validate them during Phase 0.

## 2. Agreed technical baseline

| Area | Direction |
|---|---|
| Mobile | React Native + Expo + TypeScript; iOS and Android |
| Routing | Expo Router, subject to Phase 0 confirmation during scaffold |
| API | Python + FastAPI, versioned under `/api/v1` |
| Database | PostgreSQL |
| Schema changes | Alembic migrations only |
| Architecture | Modular monolith; feature-oriented backend modules |
| Source control / CI | Existing GitHub Actions workflow is optional regression coverage during local prototyping; required branch gates follow prototype approval |
| Mobile delivery | Expo Go for the local prototype; EAS builds and store release after the final draft |
| Hosting | Local FastAPI + PostgreSQL via Docker Compose now; choose hosted API/database after prototype signoff |

Do not introduce an ORM, authentication vendor, object-storage vendor, push provider, voice vendor, or hosting provider as a settled choice until it is recorded in a short decision note. The implementation proposal is SQLAlchemy 2.x with Alembic, Pydantic settings, a managed PostgreSQL service, private object storage, and a managed real-time voice service; validate fit and current pricing before adoption.

## 3. User-facing interfaces and navigation

### Mobile navigation model

**Unauthenticated stack**

- Welcome / value proposition
- Sign up, sign in, verify email/phone as selected, password reset
- Terms, privacy, and consent entry points

**Authenticated primary tabs**

1. **Home** — joined communities, upcoming sessions, unread activity, personalized shortcuts.
2. **Discover** — search by name/topic, curated categories, filters, public community preview.
3. **Create** — create community or scheduled activity (permission-aware).
4. **Inbox** — direct and community conversations, unread state, notification preferences.
5. **Profile** — profile, memberships, saved material, settings, privacy, help, and account actions.

The exact tab layout and labels are a design validation item, not a backend constraint.

### Screen/interface inventory by domain

| Domain | Interfaces / flows |
|---|---|
| Identity | Welcome, registration/login, verification, password reset, session expiry, account recovery |
| Profile | View/edit profile, interests/topics, privacy controls, block list, account deletion |
| Communities | Discover/search/filter, preview, create/edit/archive/expire, member list, join/leave, invite link, access request |
| Roles | Founder controls, moderator assignment/removal, member permissions, ownership transfer |
| Community home | About/rules, announcements, activity feed, upcoming events, members, materials, chat entry |
| Content | Text post, link, PDF/document upload and preview, save/bookmark, delete/edit, report |
| Messaging | Conversation list, community text chat, replies, attachments where permitted, unread/read state, block/report |
| Scheduling | Event/session create/edit/cancel, calendar/list views, RSVP/notify-me, reminder controls |
| Rooms | Availability, reservation, conflict/error, reservation detail, cancellation, capacity and access controls |
| Notifications | In-app notification center, push opt-in, per-community preferences, mute/snooze |
| Moderation | Report composer, confirmation/status, moderator queue, report detail, action history, escalation queue |
| Voice | Voice room lobby, permissions/device checks, join/leave, participant state, mute/deafen, host/moderator controls, connection failure/rejoin |
| Engagement | Streak summary, activity history, reminder opt-in, pause/quiet hours, privacy controls |
| Settings/support | Notification/privacy/security settings, app preferences, FAQ/contact, legal documents, delete/export account |

Every screen contract must specify: entry point, actor/permission, input validation, loading/empty/error/offline states, analytics event (if approved), and accessibility behavior.

### Permission model

- **Platform operator:** platform-level policy and escalations, tightly restricted and audited.
- **Founder/owner:** full community administration, moderator management, ownership transfer, archive.
- **Moderator:** community-scoped member/content/report/event management as defined by policy.
- **Member:** participate and manage own content; actions depend on community access rules.
- **Visitor:** view only public preview fields and public content explicitly designated as such.

All permission checks are enforced by the API, not only hidden in the mobile UI. Define a permission matrix before the first protected write endpoint.

## 4. Backend/API interface map

The following is a planning-level resource map. Exact schemas, pagination, idempotency, and error formats are defined in Phase 0 API contracts and implemented with OpenAPI generated from FastAPI.

| Capability | Representative API surface |
|---|---|
| Auth | `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/password-reset`; verification endpoints as selected |
| Current user | `GET/PATCH /users/me`, `DELETE /users/me`, profile and privacy settings |
| Discovery | `GET /communities`, `GET /topics`, `GET /communities/{id}` |
| Communities | `POST /communities`, `PATCH/DELETE /communities/{id}`, archive/expire actions |
| Membership | `POST /communities/{id}/join`, `/leave`, access requests, member list and role actions |
| Invites | Create/revoke invite, resolve invite code/link, accept invite |
| Content | Community posts, links, comments/reactions if approved, saved items, content removal |
| Files | Upload-intent, completion, metadata, authorized download; bytes stored outside PostgreSQL |
| Messaging | Conversation list, message history/send/edit/delete, read cursor; real-time delivery channel negotiated in phase |
| Events/rooms | Event CRUD, RSVP/notify-me, availability, reservation/cancellation, reminders |
| Notifications | Notification inbox/read state, preferences, device token registration/removal |
| Moderation | Submit report, report queue/detail, action/audit record, escalation and appeal workflow |
| Voice | Voice-room/session metadata and authorized join credentials; media flows through selected voice provider |
| Health/ops | Liveness/readiness, version/build metadata, metrics and internal admin surfaces |

### API conventions

- Prefix public API routes with `/api/v1`; maintain an OpenAPI contract and compatibility policy.
- Use UUID identifiers, UTC timestamps, explicit enum values, bounded pagination, request validation, and stable error envelopes.
- Enforce object-level authorization and tenant/community scoping on every access.
- Use idempotency for retry-prone creates (payments are not currently in scope; reservations and uploads still need safe retries).
- Never include secrets, password hashes, private moderation notes, or unauthorized member data in responses.
- Use REST for normal CRUD. Add WebSocket or a managed real-time channel only for live messaging/presence; document reconnect, ordering, authorization, rate limits, and fallback behavior.

## 5. Data-domain map

Initial PostgreSQL domains (not a final physical schema):

- Identity: users, credentials/identity-provider references, sessions/refresh-token families, verification challenges, devices.
- Profile: public profile fields, interests/topics, account/privacy preferences, blocks.
- Community: communities, topics, memberships, roles/permissions, join requests, invites, lifecycle/expiry.
- Content: posts, links, comments/reactions if approved, attachments metadata, saved items.
- Communication: conversations, participants, messages, read cursors, delivery metadata.
- Scheduling: events/sessions, RSVPs, room resources, reservations, reminder jobs/subscriptions.
- Trust and safety: reports, report evidence references, moderator actions, escalation records, appeals, audit events.
- Engagement: activity ledger and streak snapshots; avoid making a streak the source of truth for other business data.
- Operations: notification outbox, idempotency records, feature flags/config where justified.

Use foreign keys, uniqueness constraints, check constraints, and indexes to encode invariants. Store uploaded binaries in private object storage and use short-lived authorized URLs. Define retention, export, deletion, and audit-log access rules before collecting sensitive data.

## 6. Target repository organization

```text
.
├── mobile/
│   ├── app/                       # Expo Router route files only
│   ├── src/
│   │   ├── features/              # auth, communities, chat, events, moderation, ...
│   │   ├── components/            # shared UI
│   │   ├── services/api/          # one typed API client
│   │   ├── config/env.ts          # validated public runtime/build config
│   │   ├── hooks/
│   │   ├── theme/
│   │   └── utils/
│   ├── assets/
│   ├── .env.example
│   ├── app.config.ts
│   └── eas.json
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── core/                  # settings, security, errors, logging
│   │   ├── db/                    # session, base, transaction helpers
│   │   ├── features/              # feature router/schema/service/repository/model
│   │   ├── integrations/          # storage, email, push, voice adapters
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── .env.example
├── infra/                         # deploy definitions and operational config
├── docs/                          # ADRs, API/security/operations documentation
├── plan/
│   ├── ROADMAP.md
│   └── phases/
├── mobile/.env.example
├── .github/workflows/
├── AGENTS.md
└── README.md
```

This is the intended structure, not a request to create all application directories before Phase 1. Keep `mobile/app` route-only. Keep generated clients/artifacts out of hand-maintained domain logic.

## 7. URL and environment workflow

During the prototype, use only the local API URL in
`mobile/.env.development.local`. Do not create public domains or EAS
environments yet. The environment matrix below is a later delivery target, not
a Phase 1 prerequisite.

### Quick local/tunnel setup

1. Copy `mobile/.env.example` to `mobile/.env.development.local` (ignored by Git).
2. Set `EXPO_PUBLIC_API_BASE_URL` to the backend API origin plus `/api/v1`. For a friend testing remotely, use the current HTTPS backend tunnel address, not a private LAN address.
3. Start the Expo development server with its tunnel option when the tester cannot reach the developer machine over LAN. Expo prints a temporary development-server URL/QR code; that is the **mobile bundle/Metro server** URL and is not the FastAPI URL.
4. Keep the backend tunnel running too. A tunnel for Expo does not automatically expose FastAPI. Update only the API base URL in the ignored env file when the backend tunnel changes, then restart/reload the Expo app so its bundled public config is refreshed.
5. Share the Expo QR/link and ensure the tester has the compatible Expo Go or project development build. Custom native features may require a development build rather than Expo Go.

### Environment matrix

| Environment | Mobile config | API/database | Delivery |
|---|---|---|---|
| Local | ignored `.env.development.local`; Expo dev server on LAN/tunnel | local API and disposable local PostgreSQL; optional temporary HTTPS tunnels | Expo Go for quick smoke tests; use a project development build for representative production-feature testing and custom native modules |
| Development | EAS development profile and development variables | isolated dev deployment and database | internal builds/OTA only when compatible |
| Staging | staging variables and staging API | isolated staging API/database/storage | internal QA/TestFlight track |
| Production | production variables supplied securely at build/release time | production API/database/storage, custom HTTPS API domain | signed app-store binaries; controlled compatible OTA updates if enabled |

Keep the tracked `.env.example` as a non-secret template. Do not commit real tunnel URLs, `.env.development.local`, signing material, API keys, or server secrets. `EXPO_PUBLIC_*` is public client configuration, not secret storage. Backend secrets belong in the deployment platform's secret manager.

The initial app is mobile, so it does not have a static frontend website URL. If a website is later added, store its canonical URL as a distinct setting; never confuse it with Expo's per-run development tunnel.

## 8. Git and release strategy

The branch rules below describe the eventual release model. During prototype
review, short-lived feature commits and local checks are sufficient; protected
branch gates and automatic deployments are deferred.

Use the requested environment branches while keeping feature work short-lived:

- `develop`: integration branch; successful merge deploys to the development environment.
- `staging`: release-candidate branch; promote tested `develop` changes here via reviewed PR; deploys to staging.
- `main`: protected production branch; promote the verified staging commit via reviewed PR/tag; production release requires approval.
- `feature/<ticket>-<short-name>` and `fix/<ticket>-<short-name>`: branch from `develop`, PR back to `develop`.
- `hotfix/<ticket>-<short-name>`: branch from `main`, PR to `main`, then forward-merge/cherry-pick the fix into `staging` and `develop`.

Protect environment branches, disallow direct pushes, require green CI and review, and record the promoted commit/build. Avoid long-lived developer-specific branches. Reassess after the team and release process are established; environment isolation should primarily come from deployment environments and secrets, not branch names alone.

Commit format: `type(scope): imperative summary`, e.g. `feat(events): add session reminders`, `fix(api): enforce community membership`, `docs(plan): define release gates`. Use `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, and `chore` consistently.

## 9. CI/CD and deployment model

This is the post-prototype target. Keep the existing checks available, but
defer required status rules, EAS delivery, cloud deployment jobs, secrets, and
automatic promotions until the owner approves the final prototype and selects
a host.

### Pull-request CI

- Mobile: install from lockfile, formatter/linter, TypeScript check, unit/component tests, Expo dependency/config diagnostics, and a production-like export/build check as feasible.
- Backend: locked dependency install, Ruff format/lint, static typing as adopted, unit/API tests, security/dependency checks.
- Database: PostgreSQL-backed integration tests; validate Alembic head and upgrade from the previous revision; fail on unexplained model/migration drift.
- Shared: secret scanning, license/dependency review policy, PR template, artifact/log retention, required status checks.

### Continuous deployment

- Merge to `develop`: deploy backend to isolated development; run migration and smoke tests; create internal mobile build when useful.
- Promote to `staging`: deploy backend to staging, migrate once, run smoke/API/mobile end-to-end tests and internal iOS/Android distribution.
- Promote/tag `main`: require approval, deploy backend with backward-compatible migration and health checks, then submit signed mobile binaries through the store release process.
- Support rollback of application images and app releases. Database rollback is not assumed safe; use forward-fix/restore plans and backward-compatible migrations.
- Keep mobile and backend release numbers/build metadata correlated. Roll out app updates gradually and monitor crashes, API errors, latency, and adoption.

### Infrastructure requirements before public launch

- Separate secrets, databases, storage buckets, push credentials, signing credentials, and access policies by environment.
- HTTPS, least-privilege IAM, private database networking where supported, rate limits, request size limits, secure headers where applicable, and restrictive CORS for any web client.
- Structured redacted logs, error reporting, service metrics, traces for critical paths, uptime/readiness checks, actionable alerts, and operational ownership.
- Automated encrypted backups with documented retention and successful restore drills; database migration and recovery runbooks.
- Privacy policy, terms, data deletion/export, account support, store metadata, permission rationale, and content moderation/report response process.

## 10. Security, privacy, and trust/safety baseline

- Passwords use a modern adaptive password hash; tokens are short-lived/rotatable and handled with platform-appropriate secure storage. Never log credentials, tokens, private message content by default, or signed URLs.
- Validate and authorize every request; apply community tenancy checks, abuse throttles, upload type/size scanning, and safe external-link handling.
- Use short-lived signed upload/download URLs for private files; verify object ownership and authorization server-side.
- Collect only necessary data; define data deletion, export, retention, and age/consent requirements before launch.
- A report threshold of five reports is a configurable **signal to queue/escalate for human review**, not automatic proof or an automatic ban. Rate-limit and deduplicate report abuse, preserve evidence with access controls, and audit moderator actions.
- Define moderation policy, emergency escalation, appeals, moderator permissions, response expectations, and safety staffing before opening communities broadly.
- Voice permissions, recording policy, blocking/reporting, room moderation, and consent must be resolved before launching voice.

## 11. Quality gates and measurable acceptance

- Critical journeys have automated tests: signup/login/session recovery, discover/join, create/invite, share/download file, message/reconnect, RSVP/reserve/cancel, report/review/escalate, voice join/leave, and reminders.
- No unresolved critical/high security finding; access-control tests prove cross-community data isolation.
- Migrations are reviewed and tested against a representative prior schema; backup restore is rehearsed before production launch.
- Mobile experience is manually tested on supported iOS and Android devices, including permission denial, poor network, app resume, and accessibility basics.
- Release candidate has no known release-blocking crashes, migration failures, or critical user-journey defects; rollback and support owners are named.
- Product metrics and retention analytics require privacy review and opt-in/notice decisions where applicable; collect no unnecessary message/file content.

## 12. Phases and exit gates

Detailed tasks, outputs, and acceptance checks are in the linked files.

| Phase | Scope | Exit gate |
|---|---|---|
| 0 — Product decisions & design contracts | Validate personas, MVP sequence, permissions, privacy/moderation policy, providers, UX/API contracts, risk decisions | Approved scope, key architecture decisions, interface map, acceptance criteria |
| 1 — Local prototype foundation | Expo Go app, local FastAPI/PostgreSQL, Alembic, local URL config, discovery and preview UI | Fresh local setup, migrated/seeded API, app-to-API smoke on iOS/Android, prototype feedback |
| 2 — Identity & onboarding | Auth, profile, sessions, account/security settings, consent/legal entry points | Secure critical identity journeys and authorization tests |
| 3 — Communities & discovery | Create/manage/search/join/leave, access rules, invites, membership roles | End-to-end discover-to-join and owner/moderator permissions |
| 4 — Content, materials & files | Posts, links, PDFs/documents, private storage, saved items, report entry points | Secure sharing and upload/download flows with limits and auditability |
| 5 — Messaging & notifications | Community conversations, real-time delivery, read/unread, push/in-app preferences | Reconnect/retry behavior, notification controls, abuse controls |
| 6 — Scheduling, rooms & reminders | Events/sessions, reservations, conflicts, RSVP/notify-me, reminders | Correct timezone, conflict/idempotency, cancel/reschedule behavior |
| 7 — Moderation & trust/safety | Reports, queues, audit, escalation, actions/appeals, operator tools | Human-review process, abuse resistance, permission/audit tests |
| 8 — Voice rooms | Provider integration, lobby, participation/host controls, failure/rejoin, safety and cost controls | Cross-platform audio QA, permission/safety policy, capacity and cost review |
| 9 — Streaks & engagement | Activity ledger, streaks, reminders, privacy/quiet hours, engagement metrics | User-controlled engagement with correct timezone and privacy semantics |
| 10 — Final identity, production readiness & launch | Confirm brand/domain/app IDs and provider/region/budget; EAS signing, hosted API/database, CI/CD protections, hardening, store release, runbooks, staged rollout | Go/no-go checklist signed, restore/rollback rehearsed, monitoring/support in place |

## 13. Open decisions register

Must be resolved in the indicated phase; absence of a choice must not block planning but does block the affected implementation.

| Decision | Proposed evaluation / default | Due |
|---|---|---|
| Product name, brand, public domain, and native app IDs | Decide after the prototype is approved; use an owned namespace for permanent store identifiers | 10 |
| Audience, age floor, initial locale | Validate launch audience and legal/privacy requirements before identity and public launch | 0/2 |
| Expo Router and state/data libraries | Prefer Expo Router; choose state, query/cache, and forms libraries based on supported versions and team comfort | 0 |
| Auth method | Compare email/password, email links, phone, and social sign-in; define verification and recovery | 0 |
| Cloud provider, region, deployment target, budget | Compare managed container hosting, managed PostgreSQL, storage, backups, data residency, and egress cost after prototype signoff | 10 |
| ORM and DB access | Validate SQLAlchemy async/sync approach, pooling, transaction boundaries, and migration tooling | 0 |
| Email, push, object storage | Pick providers and define adapters, deliverability, costs, residency, and failure policy | 0/4/5 |
| Real-time messaging | Compare managed realtime vs FastAPI WebSockets; document ordering, presence, offline, reconnect, scaling | 5 |
| Room reservation meaning | Confirm whether “room” means virtual audio room, physical/online resource booking, or both; current plan allows both domains | 6 |
| Voice service | Compare cross-platform SDKs, moderation, region/cost, recording policy, quality, and provider portability | 8 |
| Report threshold/policy | Keep five as configurable escalation threshold; define evidence, duplicate/brigading handling, actions, appeals, staffing | 0/7 |
| Branch / CI provider | GitHub Actions is the working assumption; confirm repository and store access model | 1 |
| Analytics/observability vendors | Decide minimal privacy-preserving set and retention before telemetry collection | 1/10 |

## 14. Current implementation checkpoint

Phase 1 is now explicitly local-prototype work. The Expo shell, themed Home and
Discover screens, FastAPI health endpoints, PostgreSQL/Alembic foundation,
initial users/communities revision, open-community discovery API, centralized
mobile API URL configuration, a read-only public community preview route with
native-share support and reduced-motion-aware content entrance are implemented.
A non-root backend container build definition is in place. GitHub Actions CI
includes mobile API contract tests and is configured to build/smoke-test that
image. The API adds request IDs and redacted structured access logs. The preview
link is an app deep link, not an invite link or production HTTPS universal link.
Mobile API errors surface validated request IDs as selectable support references.

Home is a guest-safe welcome and topic launcher, not a fictional joined-community
dashboard; the member dashboard remains pending identity/membership. Discover
uses the API and has loading, error, empty, search, topic-filter, and pagination
states, including pull-to-refresh that retains loaded results on refresh failure.
Its available topic filters now come from `GET /api/v1/topics`, which
lists distinct topics with active open communities; Home and Discover handle
topic loading/failure without blocking the all-communities view. The API
intentionally does not return invite-only communities until a
public-preview policy is decided. Selecting an open community shows an API-backed
preview; join/create, membership, and role actions remain out of scope until
identity and access decisions are complete. The development seed command is
explicit and refuses to run outside `APP_ENV=development`.

The first GitHub Actions run is complete. Its backend/PostgreSQL job passed the
Alembic migration, repository integration tests, and Docker image readiness
smoke test. The mobile job passed installation, Expo compatibility, unit tests,
typecheck, and web/iOS/Android exports, but failed at `npm audit` on the two
documented upstream high advisories. The initial Alembic migration and
readiness endpoint were also verified against an isolated, temporary
PostgreSQL 18 cluster; the developer's existing PostgreSQL service was not
modified. The hosted CI workflow is retained as optional regression coverage;
its audit failure is not a blocker to opening the local prototype, but must be
resolved before making remote CI a required release gate.

The mobile URL template now defaults to a local FastAPI address, and the Expo Go
instructions cover iOS Simulator, Android Emulator, and physical devices on a
trusted Wi-Fi network. EAS profiles, custom development-client builds, package
IDs, brand/domain decisions, hosted API environments, branch protections, and
production deployment are intentionally deferred until the user approves the
prototype. Remote `develop` and `staging` branch names exist as scaffolding;
feature pushes do not trigger hosted CI during prototype iteration. The user
reports inspecting the UI in Android Studio. We still need to confirm the
API-backed discovery/preview flow there and capture feedback; Expo Go access
from this Windows host is blocked by its group-policy-managed inbound firewall.

The SQLAlchemy async/asyncpg choice is provisional and recorded in
`../docs/decisions/0001-async-sqlalchemy.md`; revisit it at the Phase 0
architecture decision gate before production. Hosting, authentication, and
other product/provider decisions remain unresolved as listed above.

Phase 2 has begun with a local-only identity UI exploration: Home now links to
welcome, sign-up, and sign-in screens, with guest browsing preserved. The forms
only validate draft input in memory and explicitly do not transmit or save it;
they do not create accounts or sessions. Email/password is a provisional screen
prototype, not a chosen authentication method. Authentication, recovery,
verification, age/audience, and profile persistence remain gated on the Phase 0
decisions and owner review. A profile setup/preview screen now demonstrates a
display name and sample interest selection entirely in screen memory; its
interest taxonomy, profile visibility, and persistence are not decisions.
See `phases/PHASE-02-identity-onboarding.md`.
