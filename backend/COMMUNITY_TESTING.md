# Community API smoke testing

The examples below use the local API and a verified account. In Swagger, use
the **Authorize** button and enter the account's access token as a Bearer token.
The same endpoints can be called from a terminal with `curl.exe`.

## Create an open community

`POST /api/v1/communities`

```json
{
  "name": "GATE Study Circle",
  "topic": "Exam preparation",
  "description": "Focused peer study group.",
  "access_type": "open"
}
```

Expected: `201 Created`, with a generated URL-safe `slug`. Save that slug for
the membership examples. The first creator is persisted as the `owner`.
New slugs use a normalized readable name followed by a **public** UUID in
hexadecimal (for example, `gate-study-circle-<32-hex-public-id>`). That UUID is
separate from the internal database primary key. Responses use `public_id` or
the slug; they never return the internal primary key. The UI should display
`name`, not the slug; clients must pass the complete slug for routes.
The public preview endpoint returns `member_count`, including the owner and any
moderators or members.
Community display names are globally unique after trimming and ignoring case.
Submitting the same name again returns `409 Conflict`; choose a distinct name
instead of creating another confusing copy.

When you apply the new database migration, existing duplicate names are repaired
deterministically: the oldest keeps its current name, later duplicates receive
numeric suffixes, and existing unique names are preserved. The following
public-ID migration replaces existing slugs with the new public-UUID format;
refresh any old local test links after applying it. Internal database IDs and
primary keys are not part of community, membership, or invite responses.

## Create an invite-only community

Use the same request body with:

```json
{
  "name": "Private Study Circle",
  "topic": "Exam preparation",
  "description": "Members join by invitation.",
  "access_type": "invite_only"
}
```

Invite-only communities can receive owner-managed invitations as described
below.

## Join and leave an open community

Replace `{slug}` with the slug returned by the create endpoint:

- `POST /api/v1/communities/{slug}/join` — first join returns `201`; repeating
  it returns `200` with the existing membership.
- `DELETE /api/v1/communities/{slug}/leave` — returns `204`; repeating a leave
  for an active open community also returns `204`.
- The owner receives `409` when trying to leave. Ownership transfer must be
  implemented before that can be allowed.
- Invite-only, expired, and unknown community slugs return the same `404` to a
  non-member.

Both membership endpoints require a valid, non-revoked access token from a
verified account. Neither request has a JSON body.

## Read and update your community

- `GET /api/v1/communities/mine` lists all communities you own, including
  invite-only and expired ones. Use it to retrieve refreshed slugs after
  applying migration `0008`.
- `GET /api/v1/communities/memberships/me` lists communities the signed-in
  account currently belongs to, whether as owner, moderator, or member. It
  returns only the caller's memberships; it does not accept another user's ID.
  Expired communities are included with `community_status: "expired"`.
- `GET /api/v1/communities/{slug}/members` lists the current roster only to
  that community's owner or moderators. It includes user public IDs, display
  names, roles, and join timestamps, but never internal user IDs or email
  addresses. A regular member or unrelated account receives `403`; an unknown
  slug receives `404`. Public previews continue to show only `member_count`.
- `GET /api/v1/communities/{slug}/manage` returns a community only to its owner,
  including an invite-only community that is hidden from public preview.
- `PATCH /api/v1/communities/{slug}` updates only fields supplied in the body.
  For example:

```json
{
  "name": "GATE Study Circle — Updated",
  "topic": "GATE preparation",
  "description": "Updated community details.",
  "expires_at": null
}
```

The slug remains unchanged when the display name changes. `expires_at: null`
clears an existing expiry; if set to a timestamp, it must include a timezone
and be in the future. Empty patches and explicit nulls for name/topic/
description/access type return `422`. Authenticated non-owners receive
`403 Forbidden` with a clear authorization message; unknown slugs return
`404 Not Found`. A `403` response never includes private community data.

## Create, accept, and revoke an invite

As the community owner, create an invite-only community, then call:

`POST /api/v1/communities/{slug}/invites`

No request body is required. The response contains `invite_public_id`,
`invite_token`, and `expires_at`. The token is returned only once and is stored
as a hash in PostgreSQL. It expires after 7 days at most, or sooner if the
community expires first.

As another verified, signed-in account, accept it with:

`POST /api/v1/communities/invites/accept`

```json
{
  "invite_token": "paste-the-invite_token-returned-at-creation"
}
```

The first acceptance returns `201`; retrying as the same account returns
`200` with its existing membership. A different account trying to reuse the
token receives `409`. Invalid, expired, or revoked invites receive `404`.

Owners can inspect invite metadata without exposing tokens:

- `GET /api/v1/communities/{slug}/invites`
- `DELETE /api/v1/communities/{slug}/invites/{invite_public_id}`

Revocation returns `204` and is safe to repeat. An already accepted invite
cannot be revoked (`409`). Invite creation is limited to 10 attempts per owner
and acceptance to 20 attempts per account in the configured rate-limit window
(15 minutes by default); throttled responses include `Retry-After`.

The owner invite list and revoke endpoint use the non-secret
`invite_public_id`, not the invite table's internal primary key. The backend
returns the secret token, not a hardcoded host or app URL; the mobile client
will wrap it in the shareable deep link when invite-link UI is integrated.
For this backend smoke test, paste the token into the acceptance request above.
