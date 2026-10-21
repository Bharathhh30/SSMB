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

Invite-only communities can be created now, but invite creation and acceptance
are not implemented yet. Other users therefore cannot join one in this slice.

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
and be in the future. Empty patches, explicit nulls for name/topic/description/
access type, and edits by non-owners are rejected (`422` for invalid input;
`404` for non-owner or unknown community).
