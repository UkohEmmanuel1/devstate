# DevState Django API

PowerShell setup:

```powershell
cd backend
py -3.11 -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Routes: `/api/health/`, `/api/projects/`, `/api/projects/scan/`, `/api/events/`, `/api/events/create/`, `/api/focus/`, `/api/focus/start/`, `/api/focus/end/`, `/api/notifications/test/`, `/api/snapshots/`.

Set `DEVSTATE_PROJECTS_DIRS` to semicolon-separated local paths and configure `DEVSTATE_NTFY_TOPIC` in `.env`. Keep the API bound to localhost.
