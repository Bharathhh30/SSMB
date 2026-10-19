# ADR 0002: Email/password authentication with verified email

**Status:** Accepted by product owner on 2026-10-19
**Decision owner:** Product owner
**Scope:** First backend identity release

## Decision

- Use first-party email/password registration and sign-in.
- Require email verification before issuing an authenticated session.
- Provide a one-time, expiring password-recovery flow.
- Defer social sign-in from the first release.
- Keep email delivery behind a replaceable adapter; no SMTP/cloud mail vendor is
  selected by this decision.

## Security implementation baseline

- Hash passwords with Argon2id through `pwdlib`; never store plaintext or
  reversible passwords.
- Enforce a 15-character minimum and 1024-byte UTF-8 maximum for new passwords;
  allow spaces and do not require character-class composition. Revisit the
  user-facing wording during post-backend frontend integration.
- Normalize and validate email at the API boundary, and enforce uniqueness in
  PostgreSQL.
- Generate high-entropy, opaque verification/recovery/session tokens. Store only
  token hashes in PostgreSQL; action tokens are single-use and expire.
- Use database-backed sessions with short-lived access tokens and rotating
  refresh tokens. Detect refresh-token reuse and revoke the affected session.
- Return generic registration and recovery responses to reduce account
  enumeration. Do not log passwords, tokens, or private email contents.
- Use fake email delivery in tests. Real/local email delivery requires a
  configured adapter; do not pretend an email was sent when no adapter exists.

## Consequences

- Email delivery, sender identity, and production provider selection remain
  explicit implementation/release decisions.
- User verification and recovery tests must exercise delivery success/failure,
  expired/replayed tokens, and enumeration-resistant responses.
- Existing development seed users may have a null email until authentication
  migration and seed behavior are deliberately updated; authenticated users
  created through the API require a unique normalized email.
- This decision does not settle audience/age policy, profile visibility, legal
  consent, or production deployment.

## Implementation status

The schema migration and tested password/email/token primitives are in place.
Registration, verification, session, and recovery endpoints plus configured
email delivery are still pending; this ADR does not claim authentication is
implemented or production-ready.
