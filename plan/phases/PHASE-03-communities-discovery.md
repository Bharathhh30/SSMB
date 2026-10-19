# Phase 3 — Communities, discovery, access, and roles

**Status:** In progress (read-only discovery slices delivered ahead of the phase gate)
**Goal:** Make the core discover → join → participate journey work with enforceable community access rules.

## Backend-first sequencing

Implement and test the APIs, persistence rules, migrations, and permission
matrix first. The existing Expo discovery and preview screens are frozen; all
new community UI and mobile/API integration wait for the Backend Completion
Gate.

## Backend work

- Implement community lifecycle, topic taxonomy, public/private visibility, open/invite/request access, optional expiry, and owner controls.
- Add search/filter/pagination and a safe public preview.
- Implement join/leave, access requests if selected, shareable invite creation/revocation/acceptance, and invite abuse limits.
- Add memberships, founder/moderator/member roles, moderator assignment/removal, ownership transfer, and member roster privacy.
- Add contract tests for discovery and all community mutations; include
  anonymous/member/founder/moderator cases, cross-community access, expiry,
  invite replay/revocation, duplicates, and concurrent membership changes.

## Read-only preview slice delivered ahead of the phase gate

This completed mobile slice is preserved as-is and is not a reason to continue
frontend implementation before backend completion.

- [x] Derive the public topic filter list from active, open communities through `GET /api/v1/topics`; show retry/fallback states when the list is unavailable.
- [x] Add native pull-to-refresh for Discover while preserving loaded results when a refresh fails, with an inline retry and support reference.
- [x] Open the public community preview from Discover.
- [x] Share the preview using the native share sheet and an app deep link.
- [x] Reveal fetched preview content with reduced-motion-aware entrance motion.
- [ ] Add HTTPS universal/app links and a web fallback before production sharing; the development Expo Go URL is temporary and requires the development server to remain reachable.
- [ ] Keep invite links separate and authorization-protected when identity and membership are implemented.

## Exit criteria

- A user can create/discover/join/leave a community and invite another authorized user.
- API tests prove a community member cannot read or mutate another private community's data.
- Founder and moderator permissions follow the approved matrix and all privileged changes are auditable.
