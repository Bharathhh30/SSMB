# Phase 3 — Communities, discovery, access, and roles

**Status:** Complete — agreed community APIs, owner/moderator roster access, audited role/ownership/lifecycle/metadata operations, and reversible archive/restore are implemented and PostgreSQL-tested. Moderators are roster-read-only until Phase 7; permanent deletion and audit retention remain deferred.
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
- Add memberships, founder/moderator/member roles, moderator assignment/removal, ownership transfer, and member roster privacy. **Approved roster rule (October 22, 2026):** only the community owner and its moderators can view member identities; public/non-member views retain aggregate counts only, and arbitrary users' cross-community membership histories stay private.
- **Approved archive rule (October 22, 2026):** owner-controlled reversible archive; never hard-delete in this phase; hide archived communities from discovery/public previews, block new joins and invite acceptance, revoke active unused invites, retain memberships/data, and allow owner restore. Restored communities require fresh invites; expired communities remain undiscoverable after restore.
- **Approved moderator rule (October 22, 2026):** moderators may read their community roster, but have no community-management or enforcement write permissions until the moderation contract is implemented in Phase 7.
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

## Backend implementation progress

- [x] Add the community membership table with role and duplicate-membership
  constraints through Alembic revision `0005_community_memberships`.
- [x] Implement `POST /api/v1/communities` for verified authenticated users,
  supporting the agreed `open` and `invite_only` access types.
- [x] Normalize request text, validate expiry timestamps, generate URL-safe
  slugs, and avoid collisions for repeated community names.
- [x] Create the community and its founder/owner membership atomically.
- [x] Return an allowlisted community response without exposing the owner ID.
- [x] Test anonymous requests, request validation boundaries, duplicate-name
  slugs, and persisted founder membership against PostgreSQL.
- [x] Enforce globally unique community names after trimming and ignoring case;
  reject duplicates with `409` and repair historical duplicates in migration
  `0007_unique_community_names` without changing IDs or slugs.
- [x] Make each newly created slug a readable normalized-name prefix plus the
  full public UUID, separate from the database primary key.
- [x] Return public identifiers instead of internal user/community/invite
  primary keys; rotate pre-existing community slugs during migration
  `0008_public_resource_ids`. The UI displays the community name and passes
  the full slug in API routes.
- [x] Implement idempotent joins for active open communities and member leave;
  serialize concurrent joins using a community row lock and enforce the
  membership uniqueness constraint in PostgreSQL.
- [x] Hide invite-only and expired communities from non-member join/leave
  attempts; prevent the owner from leaving before ownership transfer exists.
- [x] Add owner-only management read and metadata update; preserve community
  slugs when names change and allow owners to clear an optional expiry.
- [x] Add a paginated owner-community list so owners can recover current slugs
  for private/expired communities without exposing internal primary keys.
- [x] Add a self-only paginated membership list covering owner, moderator, and
  member roles; do not expose arbitrary users' membership graphs.
- [x] PostgreSQL-test the self-membership route's caller scoping, owner/member
  roles, expired-community status, pagination completeness, and public-field
  response boundary.
- [x] Add a paginated community-roster endpoint restricted to the owner and
  moderators; include only user public IDs, display names, roles, and join
  timestamps. Members, unrelated users, and other community owners receive
  `403`; unknown communities return `404`.
- [x] PostgreSQL-test roster authorization, invite-only/expired community
  access for authorized roles, cross-community isolation, pagination, and
  response-field allowlisting.
- [x] Allow only owners to promote an existing member to moderator or demote
  an existing moderator to member; forbid changing the owner through this API.
- [x] Make role changes idempotent, serialize concurrent changes, and persist
  append-style audit events with actor/target/community references and public
  identifier snapshots. No-op role writes do not create audit events.
- [x] PostgreSQL-test owner/non-owner authorization, target scoping, owner
  protection, validation, idempotency, concurrency, audit contents, and the
  `0009_community_role_audit` migration.
- [x] Keep moderators read-only in community management during Phase 3:
  allow roster reads but deny metadata, role, invite, archive, and ownership
  mutations. Defer moderation/enforcement writes to Phase 7.
- [x] Audit metadata changes by actor and changed field names without storing
  text values; avoid duplicate audit events for no-op patches.
- [x] Record the actor for manual and archive-triggered invite revocation.
- [x] PostgreSQL-test the moderator read-only matrix and metadata/invite audit
  attribution, including no-op metadata patches.
- [x] Audit owner metadata updates by actor and changed field names without
  copying community text values into the audit log; identical-value patches
  create no duplicate event.
- [x] Record the actor who revokes an invite, including active invites revoked
  as part of community archiving.
- [x] Allow only the current owner to transfer ownership to an existing member
  of the same community; promote the target to owner and make the former owner
  a regular member.
- [x] Serialize concurrent transfers, atomically update the community and both
  memberships, and persist a separate ownership-change audit record.
- [x] Enforce at most one owner membership per community with a PostgreSQL
  partial unique index in Alembic `0010_ownership_transfer`.
- [x] PostgreSQL-test self/non-member/cross-community targets, owner-only
  access, concurrent transfers, resulting roles, leave permissions, audit
  snapshots, and migration upgrade/downgrade/re-upgrade.
- [x] Add owner-only archive and restore operations; keep archived communities
  and memberships for owner/member reads while hiding them from public
  discovery and previews.
- [x] Block joins and invite acceptance while archived; revoke active unused
  invites on archive and require fresh invites after restore.
- [x] Record archive/restore audit events and make repeated archive/restore
  operations idempotent.
- [x] PostgreSQL-test discovery/topic/preview visibility, retained membership
  status, owner/member leave behavior, invite revocation and restore behavior,
  audit events, and the `0011_community_archive` migration.
- [x] Include the current owner/moderator/member total in the public community
  detail response without exposing member identities.
- [x] Distinguish authenticated management denial (`403`) from a missing
  community (`404`) and document response meanings in OpenAPI.
- [x] Add owner-created, single-use, revocable invite tokens with a seven-day
  maximum lifetime and verified-account acceptance.
- [x] Persist only invite-token hashes; expose invite metadata without secrets,
  support idempotent same-user acceptance, and prevent cross-user replay.
- [x] Rate-limit invite creation and acceptance using the shared HMAC-backed
  PostgreSQL rate-limit store.
- [x] Define and implement the reversible archive lifecycle; permanent
  community deletion remains out of scope for this phase.
- [x] Keep arbitrary profile-to-community membership lookup private; the
  cross-community membership endpoint is self-scoped only.

Permanent community deletion and access requests are deferred, not silently
removed from the product backlog. Moderator enforcement writes are deferred to
Phase 7; until then, moderators may only read their community roster. Role,
ownership, lifecycle, and metadata audit histories store public-identifier
snapshots; retention/anonymization policy remains a production/account-deletion
decision. With those explicit gates, the Phase 3 backend scope is complete.
Invite policy is approved: owner-created, single-use, revocable tokens,
expiring within seven days, accepted only by verified signed-in accounts.

Open membership is available immediately. Invite-only communities can now
receive owner-managed invitations; the Expo share-link UI remains deferred
until backend phase integration.
