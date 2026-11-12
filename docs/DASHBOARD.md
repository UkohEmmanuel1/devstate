# DevState dashboard

The frontend is a lightweight, responsive dashboard in `frontend/index.html`. It uses vanilla HTML, CSS and JavaScript to keep the local desktop footprint small.

## Run locally

Start the backend in one terminal:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
# Configure DEVSTATE_PROJECTS_DIRS and ntfy settings
devstate
```

Start the dashboard in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. The dashboard polls the local API every 15 seconds. If the API is unavailable it clearly labels its sample data as demo mode.

Set `VITE_DEVSTATE_API` only if your API uses a different origin. The backend CORS allowlist permits the local Vite origin. Do not expose the unauthenticated API to a public network.
