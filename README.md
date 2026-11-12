# DevState

A local-first Windows developer workspace companion. The first milestone provides repository snapshots, focus-block controls, event routing, a local API, and optional phone push notifications.

## Phone notifications (ntfy)

1. Install **ntfy** on Android or iOS.
2. Create a long, unguessable topic (24+ random characters) and subscribe to it in the app.
3. Copy `.env.example` to `.env`; set `DEVSTATE_NTFY_TOPIC` to that exact topic.
4. Optionally configure an authenticated self-hosted ntfy server and token.
5. Run DevState and use `POST /notifications/test` to send a test.

A topic on public ntfy.sh is protected only by obscurity. Anyone who learns it may read or publish to it. Use a private authenticated server for sensitive use. Notification bodies intentionally contain only event summaries; do not send secrets or source code.

## Windows quick start

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
# Edit .env: set DEVSTATE_PROJECTS_DIRS and phone notification topic
devstate
```

Open http://127.0.0.1:8765/docs

## Current scope

- Discover Git repositories one level below configured project roots.
- Capture branch, HEAD commit and dirty/untracked paths.
- Persist snapshots/events in SQLite and write Markdown recovery notes.
- Start/end a focus block and route P0/P1 alerts to phone.
- Provide local FastAPI endpoints for future desktop UI and watcher integrations.

This initial version does not silently change Windows DND, kill apps, execute shell commands, commit/push/reset repositories, or run background watchers. Those require explicit, separately tested adapters.

## Configuration

See `.env.example`. Keep the API bound to localhost. Keep `.env` private.
