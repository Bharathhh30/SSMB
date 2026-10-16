# Phase 1 — Local prototype foundation

**Status:** In progress — local-first; production delivery is deferred until the prototype is approved.
**Goal:** Make the Expo app and FastAPI/PostgreSQL backend easy to run locally so the user can inspect the experience and guide iterative improvements.

## Work

- Keep the Expo/TypeScript app runnable in Expo Go on iOS and Android without a cloud project or store identifiers.
- Document local PostgreSQL startup, Alembic migration, deterministic development seed, FastAPI readiness, and the mobile API URL for simulator, emulator, or a phone on the same Wi-Fi.
- Iterate on the local discover → public preview flow, with loading, empty, error, retry, and accessibility behavior.
- Keep formatting, type, unit, backend integration, and Expo export checks easy to run locally. The existing GitHub Actions workflow remains a useful optional regression check.

## Deferred until the prototype is approved

- Product brand, public domain, permanent iOS bundle ID, and Android application ID.
- EAS project linking, custom development clients, signing credentials, store accounts, and releases.
- Hosted API/PostgreSQL, deployment regions, paid cloud resources, remote tunnels for friends, and production environments.
- Required branch protections and automatic deployments. Existing branches/workflows are scaffolding only during local prototyping.

## Deliverables

- Reproducible local Expo/FastAPI/PostgreSQL setup with a tested migration and seeded prototype communities.
- Developer can change a local API URL in `mobile/.env.development.local` without editing screens or source constants.
- User can open the prototype in Expo Go and review Discover and a public community preview before any deployment decisions.

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
- [x] Apply the initial migration and run the backend suite against an isolated temporary local PostgreSQL cluster; verify `/api/v1/health/ready` against that migrated database.
- [x] Make the local API URL template point to the backend on the same machine by default and document Android-emulator/physical-device overrides.
- [ ] Run the documented two-terminal local startup on the user's computer and open the app in Expo Go on a target iOS/Android device.
- [ ] Review the local discovery and community-preview experience with the user and iterate from their feedback.
- [ ] Before remote CI becomes a required gate, resolve the two unpatched mobile audit findings or record an owner-approved, time-bounded disposition; see `docs/security/MOBILE-NPM-AUDIT-2026-10-16.md`.

## Exit criteria

- Clean checkout can start PostgreSQL, apply the migration, seed demo data, and start FastAPI using documented local commands.
- Expo Go can reach the local API on a simulator/emulator or a phone on the same trusted network.
- The user has inspected the local app and the first prototype iteration is accepted before cloud/domain/store decisions begin.
