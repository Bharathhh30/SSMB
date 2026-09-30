# Phase 3 — Communities, discovery, access, and roles

**Status:** Not started
**Goal:** Make the core discover → join → participate journey work with enforceable community access rules.

## Work

- Implement community lifecycle, topic taxonomy, public/private visibility, open/invite/request access, optional expiry, and owner controls.
- Add search/filter/pagination and a safe public preview.
- Implement join/leave, access requests if selected, shareable invite creation/revocation/acceptance, and invite abuse limits.
- Add memberships, founder/moderator/member roles, moderator assignment/removal, ownership transfer, and member roster privacy.
- Build discovery, community preview, create/edit, join/request, invite, member list, and community home interfaces.

## Exit criteria

- A user can create/discover/join/leave a community and invite another authorized user.
- API tests prove a community member cannot read or mutate another private community's data.
- Founder and moderator permissions follow the approved matrix and all privileged changes are auditable.
