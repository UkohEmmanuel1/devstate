# DevState

DevState is an authenticated, cloud-ready and self-hostable engineering workspace. It combines Next.js/TypeScript, Clerk identity, Django REST Framework and PostgreSQL for production persistence. Repository telemetry, focus sessions, event history, recovery snapshots, domain/DNS monitoring, hosting checks and AI subscription renewal tracking are retained.

## Architecture
- `frontend/`: Next.js App Router, Clerk and a same-origin authenticated API proxy.
- `backend/`: Django, DRF, Clerk JWT/JWKS verification, owner-scoped models and ntfy notifications.
- PostgreSQL via `DATABASE_URL` in production; SQLite only for local development.
- Ownership is derived from the verified Clerk subject, never from request parameters or payloads.

## Clerk setup
1. Create a Clerk application; configure sign-in and sign-up routes as `/sign-in` and `/sign-up`.
2. Put the publishable key and server-only secret key in `frontend/.env.local`. Never expose `CLERK_SECRET_KEY` to the browser.
3. Copy the Clerk Frontend API issuer and JWKS URL into `backend/.env`.
4. Set authorized parties to exact frontend origins.

## Environment
Frontend: `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `DEVSTATE_API_URL`. Backend: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL`, `CLERK_ISSUER`, `CLERK_JWKS_URL`, optional `CLERK_AUDIENCE`, `CLERK_AUTHORIZED_PARTIES`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, and ntfy settings. See both env examples.

## Local development (PowerShell)
```powershell
cd backend
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Set DJANGO_DEBUG=true, real Clerk issuer/JWKS values and a strong DJANGO_SECRET_KEY.
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```
In another terminal:
```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
# Set Clerk keys and DEVSTATE_API_URL=http://127.0.0.1:8000/api/
npm run dev
```
Visit `http://localhost:3000`; the public landing page links to `/dashboard`.

## Production deployment
1. Provision PostgreSQL and set `DATABASE_URL`.
2. Set `DJANGO_DEBUG=false`, strong Django secret, exact `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` and HTTPS `CSRF_TRUSTED_ORIGINS`.
3. Set Clerk production keys, issuer/JWKS URL and exact authorized parties.
4. Set frontend `DEVSTATE_API_URL` to the private backend URL. Prefer exposing only Next.js publicly.
5. Run `python manage.py migrate` and `python manage.py check --deploy`; serve Django behind a correctly configured HTTPS reverse proxy.
6. Configure secrets in the hosting platform, never in Git. Verify HTTPS before enforcing redirect/HSTS.

## Security model
Django verifies Clerk RS256 JWT signatures against cached JWKS and validates issuer, expiry, not-before when present, subject, optional audience and configured authorized party. A local profile maps verified `sub` to a Django user. DRF defaults to authenticated access; only health is public. Every user-owned queryset is filtered by `request.user`; creates assign ownership server-side. Next.js obtains the Clerk token server-side and forwards it through a same-origin proxy. Production CORS/CSRF origins must be explicit allowlists. Secure cookies and proxy HTTPS settings are enabled for production. Per-account ntfy topics are HMAC-derived; public ntfy topics act as bearer capabilities, so do not disclose topic names or send credentials, secrets or private source code.

## Migration and rollout
Back up the database before deployment. Migration `0003_user_ownership` assigns existing records to an inactive `legacy-unassigned` account, preserving them without exposing them to new users. Reassignment must be an explicit, audited admin action after ownership verification. Deploy backend and secrets first, run migrations, then deploy frontend. Confirm unauthenticated API calls return 401 and cross-account object IDs return 404 before enabling traffic.

## Infrastructure and subscriptions
Domain assets, DNS checks, hosting checks, AI subscriptions, renewal summaries and the `check_renewals` management command from `feature/infrastructure-subscriptions` are preserved and user-scoped. See `docs/INFRASTRUCTURE-SUBSCRIPTIONS.md`.
