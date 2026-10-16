# Community — local prototype

The current goal is to run the app locally, inspect the experience, and iterate
from feedback. No public domain, permanent app-store IDs, EAS project, paid
hosting, or deployment setup is needed for this prototype.

## Prerequisites

- Node.js/npm for the Expo app.
- Python 3.12 and `uv` for the API.
- Docker Desktop running for the local PostgreSQL Compose service.

## 1. Start the local API and database

Use a first terminal from the repository root:

```powershell
Set-Location backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv sync --locked
docker compose up -d db
uv run --locked alembic upgrade head
uv run --locked python -m app.scripts.seed_development
uv run --locked uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --no-access-log
```

This starts a disposable local PostgreSQL database and seeds demo communities.
The database port is loopback-only and must not be exposed to a phone or tunnel.
Binding FastAPI to `0.0.0.0` lets a physical device on the same trusted Wi-Fi
reach it; keep this development server off public networks.

Check API readiness at `http://127.0.0.1:8000/api/v1/health/ready`.
Development API docs are at `http://127.0.0.1:8000/docs`.

## 2. Start Expo Go

Use a second terminal:

```powershell
Set-Location mobile
if (-not (Test-Path .env.development.local)) {
  Copy-Item .env.example .env.development.local
}
notepad .env.development.local
npm ci
npm run start -- --go --lan
```

Set `EXPO_PUBLIC_API_BASE_URL` in `.env.development.local` for the device you
are using:

| Where Expo Go runs | Local API URL |
|---|---|
| iOS Simulator on the development Mac | `http://127.0.0.1:8000/api/v1` |
| Android emulator | `http://10.0.2.2:8000/api/v1` |
| Physical iPhone or Android phone | `http://<computer-LAN-IP>:8000/api/v1` |

For a physical phone, keep it and the computer on the same trusted Wi-Fi.
`localhost` on a phone means the phone itself. Find the computer's LAN address
with `ipconfig` on Windows. Scan Expo's QR code with Expo Go.

The Expo/Metro address and API address are different. For this local prototype,
the LAN connection is enough; if local networking fails, troubleshoot it before
introducing tunnels or hosted services.

## 3. Prototype checks

```powershell
Set-Location mobile
npm run typecheck
npm run test:unit
```

The first review flow is **Home → Discover → public community preview**.
Membership and write actions are intentionally absent until identity and
permissions are designed. Give feedback on layout, language, navigation, and
the discovery/preview flow before we finalize the product identity or deploy.

More backend commands and migration guidance are in `backend/README.md`;
device-specific API URL notes are in `mobile/URLS.md`.
