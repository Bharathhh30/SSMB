# Phase 1 — Engineering foundation and delivery pipeline

**Status:** In progress
**Goal:** Establish a reproducible Expo/FastAPI/PostgreSQL codebase, safe environments, migration workflow, and CI/CD before feature work.

## Work

- Create the agreed monorepo structure; initialize Expo + TypeScript and FastAPI with locked dependencies.
- Add environment validation, `.env.example` files, ignore rules, typed mobile URL configuration, and safe logging defaults.
- Add PostgreSQL local development, migrations with Alembic, health/readiness endpoints, structured logs, and baseline metrics.
- Establish `develop`, `staging`, and protected `main` promotion branches plus short-lived feature/fix/hotfix branches and PR templates.
- Build PR workflows for formatting, lint, type checks, unit/integration tests, Expo diagnostics/build validation, migration validation, dependency/security scans.
- Create isolated development/staging/production configuration and deploy targets; initially deploy a backend health endpoint.
- Set up EAS project/build profiles and an internal development build early enough to validate real project behavior; Expo Go may be used for quick initial smoke tests but is not the production validation target. Keep provider credentials in managed secrets.
- Document local commands, tunnel-sharing steps, troubleshooting, release process, and rollback constraints.

## Deliverables

- Working app shell on iOS and Android, backend skeleton, PostgreSQL service, first Alembic revision, CI workflows, environment matrix, local setup guide.
- Developer can change the backend tunnel URL in `mobile/.env.development.local` without editing screens or source constants.

## Progress checkpoint

- [x] Expo Router tabs scaffold created with TypeScript and the current SDK-compatible Reanimated/worklets dependencies.
- [x] Dependencies locked; transitive overrides applied for the scaffold audit advisories.
- [x] Clean `npm ci`, Expo SDK compatibility check, Expo Doctor, TypeScript, mobile unit tests, and web/iOS/Android JavaScript exports pass.
- [x] Replace template screens with a themed, guest-safe Home and API-backed Discover flow.
- [x] Remove fixture membership claims and provide topic shortcuts until identity/membership exists.
- [x] Add the FastAPI health/discovery API, PostgreSQL configuration, initial users/communities schema, Alembic revision, and explicit development seed.
- [x] Add typed mobile API URL configuration, request/error handling, and a GitHub Actions PR workflow with a PostgreSQL service.
- [x] Add mobile API contract unit tests and wire them into pull-request CI.
- [x] Surface validated server request IDs as selectable references in mobile API error states.
- [x] Add a non-root API container image and CI build/readiness smoke-test definition.
- [x] Add request IDs and redacted structured HTTP logs with a generic unexpected-error response.
- [x] Install the SDK-compatible Expo development client and define development, preview/staging, and production EAS build profiles.
- [x] Apply the initial migration and run the backend suite against an isolated temporary local PostgreSQL cluster; verify `/api/v1/health/ready` against that migrated database.
- [ ] Clear or obtain an explicit, time-bounded risk disposition for the two high-severity upstream mobile dependency advisories documented in `docs/security/MOBILE-NPM-AUDIT-2026-10-16.md`; do not suppress the audit.
- [ ] Link EAS to the owner's project, choose permanent iOS/Android application IDs, provision EAS environments/signing, and build/install internal iOS and Android development clients.
- [ ] Confirm the first GitHub Actions run passes, including the PostgreSQL repository integration test.
- [ ] Resolve the two unpatched high mobile dependency advisories or record an owner-approved, time-bounded disposition; see `docs/security/MOBILE-NPM-AUDIT-2026-10-16.md`. The audit remains fail-closed.
- [ ] Configure required branch protections and environment-specific API deployment targets/secrets; hosting provider, region, and budget remain undecided.
- [ ] Smoke-test a physical-device app-to-API connection using a current backend tunnel URL.

## Exit criteria

- Clean checkout can be set up from documented steps; no credentials are needed in tracked files.
- CI is required on PRs and exercises both app and API.
- A tested migration can run locally and in development as a single controlled step.
- Expo development server and FastAPI are independently reachable for remote testing; staging and production are isolated.
