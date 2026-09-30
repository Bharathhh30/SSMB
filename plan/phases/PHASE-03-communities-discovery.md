# Phase 3 — Communities, discovery, access, and roles

**Status:** In progress (read-only discovery slices delivered ahead of the phase gate)
**Goal:** Make the core discover → join → participate journey work with enforceable community access rules.

## Work

- Implement community lifecycle, topic taxonomy, public/private visibility, open/invite/request access, optional expiry, and owner controls.
- Add search/filter/pagination and a safe public preview.
- Allow visitors to share the public preview route; keep it distinct from authorized invite links.
- Implement join/leave, access requests if selected, shareable invite creation/revocation/acceptance, and invite abuse limits.
- Add memberships, founder/moderator/member roles, moderator assignment/removal, ownership transfer, and member roster privacy.
- Build discovery, community preview, create/edit, join/request, invite, member list, and community home interfaces.

## Read-only preview slice delivered ahead of the phase gate

- [x] Derive the public topic filter list from active, open communities through `GET /api/v1/topics`; show retry/fallback states when the list is unavailable.
- [x] Open the public community preview from Discover.
- [x] Share the preview using the native share sheet and an app deep link.
- [x] Reveal fetched preview content with reduced-motion-aware entrance motion.
- [ ] Add HTTPS universal/app links and a web fallback before production sharing; the development Expo Go URL is temporary and requires the development server to remain reachable.
- [ ] Keep invite links separate and authorization-protected when identity and membership are implemented.

## Exit criteria

- A user can create/discover/join/leave a community and invite another authorized user.
- API tests prove a community member cannot read or mutate another private community's data.
- Founder and moderator permissions follow the approved matrix and all privileged changes are auditable.
