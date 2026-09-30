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
- [x] TypeScript, Expo dependency alignment, Expo Doctor, dependency audit, and web static export pass.
- [x] Replace template demo screens with themed Home and API-backed Discover flows.
- [x] Add the FastAPI health/discovery API, PostgreSQL configuration, initial users/communities schema, Alembic revision, and explicit development seed.
- [x] Add typed mobile API URL configuration, request/error handling, and a GitHub Actions PR workflow with a PostgreSQL service.
- [ ] Run the migration and readiness endpoint against the developer's live local PostgreSQL service.
- [ ] Confirm the first GitHub Actions run passes, including the PostgreSQL repository integration test.
- [ ] Configure required branch protections, environment-specific deployment targets/secrets, and EAS build profiles.
- [ ] Smoke-test a physical-device app-to-API connection using a current backend tunnel URL.

## Exit criteria

- Clean checkout can be set up from documented steps; no credentials are needed in tracked files.
- CI is required on PRs and exercises both app and API.
- A tested migration can run locally and in development as a single controlled step.
- Expo development server and FastAPI are independently reachable for remote testing; staging and production are isolated.
