# DevState

DevState is a local-first developer workspace companion. The current stack is **Next.js + TypeScript** for the dashboard and **Django + Django REST Framework** for the API.

## Architecture

- `frontend/` — Next.js App Router, TypeScript, Tailwind CSS and Lucide icons.
- `backend/` — Django, Django REST Framework, SQLite and ntfy phone push notifications.
- Dashboard polls the local Django API every 15 seconds and exposes repository, focus-session, event and recovery-snapshot controls. The Infrastructure page tracks domains, hosting endpoints, renewal dates and AI subscriptions.

## Run the Django backend (PowerShell)

```powershell
cd backend
py -3.11 -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

## Run the Next.js dashboard (second terminal)

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open http://127.0.0.1:3000. See `backend/README.md` for API configuration and `docs/DASHBOARD.md` for frontend setup.

## Phone notifications

Install ntfy on Android or iOS. Subscribe to a private, unpredictable topic and set `DEVSTATE_NTFY_TOPIC` in `backend/.env`. Optionally configure `DEVSTATE_NTFY_TOKEN` for an authenticated ntfy server. Restart Django and use the dashboard's **Send phone test** action.

A public ntfy.sh topic is only protected by secrecy of its name. Anyone who learns the topic can potentially read or publish messages. Do not send secrets, credentials or source code in notifications.

## API routes

- `GET /api/health/`
- `GET /api/projects/` and `POST /api/projects/scan/`
- `GET /api/events/` and `POST /api/events/create/`
- `GET /api/focus/`, `POST /api/focus/start/`, `POST /api/focus/end/`
- `GET/POST /api/domains/` and `POST /api/domains/{id}/check_dns/`
- `GET/POST /api/hosting/` and `POST /api/hosting/{id}/check/`
- `GET/POST /api/ai-subscriptions/`
- `GET /api/renewals/` and `POST /api/infrastructure/check/`
- `POST /api/notifications/test/`
- `POST /api/snapshots/`

## Current implementation boundary

This is an initial application foundation. The repository scanner checks configured roots and their immediate child directories. GitHub CI webhooks, Google Calendar, Windows focus/DND integration, background watchers and the full desktop agent are future milestones. Keep Django bound to localhost while the API has no authentication configured.
