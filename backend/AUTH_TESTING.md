# Authentication API test guide

This guide exercises the backend directly; it does not require the mobile app or
Swagger.

## Start local services

From `backend/` in PowerShell:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv sync --locked
docker compose up -d db mailpit
uv run --locked alembic upgrade head
uv run --locked python -m app.scripts.seed_development
uv run --locked uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

Keep that terminal running. In a second PowerShell terminal:

```powershell
Set-Location backend
.\scripts\smoke-auth.ps1
```

The script generates a unique local test email and sends all verification and
recovery mail to the local Mailpit catcher at `http://127.0.0.1:8025`; it does
not contact external email addresses. It verifies registration, one-time email
verification, sign-in, `/me`, private profile update, refresh rotation/replay
revocation, password recovery, and sign-out.

The generated account remains in the development database. Use a disposable
database if you do not want test accounts retained.

## Copy/paste request payloads

These are the exact JSON shapes used by the script. Replace the example email
and token values. Verification/reset tokens are in the matching Mailpit email.

**Register**

```json
{
  "email": "backend-test@example.com",
  "password": "Local-Only-Passphrase-2026!",
  "display_name": "Backend Test"
}
```

**Verify email**

```json
{
  "token": "copy-the-verification-token-from-mailpit"
}
```

**Sign in**

```json
{
  "email": "backend-test@example.com",
  "password": "Local-Only-Passphrase-2026!"
}
```

Use the returned `access_token` as `Authorization: Bearer <token>` for
`GET /api/v1/auth/me` and `POST /api/v1/auth/logout`.

**Read private self-profile**

```http
GET /api/v1/profile/me
Authorization: Bearer <access_token>
```

**Update display name and private interests**

```json
{
  "display_name": "Backend Test",
  "interests": ["Exam prep", "Technology"]
}
```

Send that body to `PATCH /api/v1/profile/me` with the same bearer token.
Interests are free-form, private to the account, and case-insensitive duplicate
values are rejected; no public profile-visibility policy is implied.

**Refresh**

```json
{
  "refresh_token": "copy-the-refresh_token-from-login"
}
```

**Request recovery**

```json
{
  "email": "backend-test@example.com"
}
```

**Reset password**

```json
{
  "token": "copy-the-password-reset-token-from-mailpit",
  "new_password": "Reset-Only-Passphrase-2026!"
}
```

## Expected negative cases

- Invalid email, blank display name, or password shorter than 15 characters:
  `422`.
- Sign-in before verification or with an incorrect password: generic `401`.
- Reused or invalid verification/reset token: generic `400`.
- Replayed refresh token: `401` and the rotated session is revoked.
- Repeated login/email/token attempts: `429` with a `Retry-After` header once
  the configured rate-limit window is exceeded.
- Expired verification, recovery, access, or refresh token: rejected; no
  account/session mutation is accepted.
- Empty profile patches, blank display names/interests, duplicate interests,
  more than 20 interests, and unknown fields: `422`.
- `GET /api/v1/profile/me` and `PATCH /api/v1/profile/me` without a valid
  bearer token: `401`.
- Old password after recovery: generic `401`.
- Access token after sign-out: `401`.
