# DevState

DevState is an authenticated, cloud-ready and self-hostable engineering workspace. It combines Next.js/TypeScript, Clerk identity, Django REST Framework and PostgreSQL for production persistence. Repository telemetry, focus sessions, event history, recovery snapshots, domain/DNS monitoring, hosting checks and AI subscription renewal tracking are retained.

## Architecture

- `frontend/`: Next.js App Router, Clerk and a same-origin authenticated API proxy.
- `backend/`: Django, DRF, Clerk JWT/JWKS verification, owner-scoped models, rate limits and ntfy notifications.\n- `src/devstate/`: legacy standalone Python event router/SQLite package; it is not the Django web runtime or system of record.
- PostgreSQL via `DATABASE_URL` in production; SQLite is supported for local development.
- S3-compatible private object storage is required for production recovery snapshots.
- Production hosting checks require a controlled outbound egress proxy. The proxy must enforce destination-IP policy at connection time.
- Ownership is derived from the verified Clerk subject, never from request parameters or payloads.

See `docs/ARCHITECTURE.md` for component responsibilities, request flow, trust boundaries and the legacy package boundary.\n\n## Clerk setup

1. Create a Clerk application and configure sign-in and sign-up routes as `/sign-in` and `/sign-up`.
2. Put the publishable key and server-only secret key in `frontend/.env.local`. Never expose `CLERK_SECRET_KEY` to browser code.
3. Copy the Clerk Frontend API issuer and JWKS URL into `backend/.env`.
4. Configure authorized parties as exact frontend origins. When the allowlist is set, the backend requires a matching `azp` claim.
5. Use separate Clerk development and production instances.

## Environment variables

Frontend:
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY` (server-only)
- `DEVSTATE_API_URL` (private backend URL)

Backend:
- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- `DATABASE_URL`
- `CLERK_ISSUER`, `CLERK_JWKS_URL`, optional `CLERK_AUDIENCE`, `CLERK_AUTHORIZED_PARTIES`
- `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`
- `DEVSTATE_EGRESS_PROXY_URL` for production hosting checks
- `DEVSTATE_SNAPSHOT_BUCKET`, optional `DEVSTATE_SNAPSHOT_REGION` and `DEVSTATE_SNAPSHOT_ENDPOINT` for private S3-compatible snapshots
- `DEVSTATE_NTFY_SERVER`, `DEVSTATE_NTFY_TOPIC_PREFIX`, `DEVSTATE_NTFY_TOPIC_SECRET`, optional `DEVSTATE_NTFY_TOKEN`
- `API_ANON_RATE`, `API_USER_RATE`, `API_PROJECT_SCAN_RATE`, `API_SNAPSHOT_RATE`, `API_NOTIFICATION_RATE`, `API_INFRASTRUCTURE_CHECK_RATE`\n- Optional error tracking: `SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE`, `SENTRY_ENVIRONMENT`

See `frontend/.env.example` and `backend/.env.example`. Never commit `.env`, `.env.local`, credentials or production secrets.

## Local development (PowerShell)

Backend:
```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Set DJANGO_DEBUG=true, Clerk issuer/JWKS values and a strong DJANGO_SECRET_KEY.
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Frontend, in a second terminal:
```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
# Set Clerk keys and DEVSTATE_API_URL=http://127.0.0.1:8000/api/
npm run dev
```

Visit `http://localhost:3000`. The landing page is public; dashboard and app routes require a Clerk session.

## Docker Compose

A local Compose stack is provided for the frontend, Django API and PostgreSQL. Create `backend/.env` and `frontend/.env.local` from their examples. Create a root `.env` containing `POSTGRES_PASSWORD` and `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`; keep it untracked. Configure real Clerk development values in the two service env files.

```powershell
$env:POSTGRES_PASSWORD = "replace-with-a-local-database-password"
$env:NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_test_your_clerk_publishable_key"
docker compose up --build -d
docker compose exec api python manage.py migrate
```

The Django API is internal to the Compose network; the Next.js application is exposed on port 3000. This Compose file intentionally runs Django in DEBUG mode for local development. Do not expose this configuration directly to the public internet or treat it as a hardened production deployment. Production requires managed secrets, private object storage, an enforced egress proxy, backups and TLS termination.

## Production deployment

1. Provision PostgreSQL, private S3-compatible object storage and a controlled outbound egress proxy.
2. Configure `DATABASE_URL`, `DEVSTATE_SNAPSHOT_BUCKET` and `DEVSTATE_EGRESS_PROXY_URL`. The egress proxy must block loopback, private, link-local, reserved and cloud metadata destinations after DNS resolution at connection time.
3. Set `DJANGO_DEBUG=false`, a strong Django secret, explicit `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` and HTTPS `CSRF_TRUSTED_ORIGINS`.
4. Set Clerk production keys, issuer/JWKS URL and exact authorized parties.
5. Set frontend `DEVSTATE_API_URL` to the private backend URL. Prefer exposing only Next.js publicly.
6. Run `python manage.py check --deploy`, `python manage.py migrate`, and deploy Django behind a correctly configured HTTPS reverse proxy.
7. Configure daily `python manage.py check_renewals` execution using the platform scheduler. The notification ledger prevents concurrent duplicate deliveries and retries pending notifications.
8. Configure automated PostgreSQL backups, private object-storage lifecycle policies, monitoring and a tested restoration procedure before opening access to customers.

## Security model

Django verifies Clerk RS256 JWT signatures against cached JWKS and validates issuer, expiry, not-before when present, subject, optional audience and configured authorized party. A local profile maps the verified `sub` to a Django user. DRF defaults to authenticated access; only the health endpoint is public. Every user-owned queryset is filtered by `request.user`; creates assign ownership server-side.

Next.js obtains the Clerk token server-side and forwards it through a same-origin proxy. The browser does not receive the Django bearer token or Clerk secret key. Production CORS/CSRF origins must be explicit allowlists. Secure cookies, HTTPS redirects, HSTS and proxy SSL handling are enabled in production configuration. API throttles apply globally and more tightly to repository scans, snapshots, notifications and infrastructure checks.

Repository scanning is limited to configured per-account roots and rejects symlinked account roots and repository paths that escape the account directory. Production hosting checks are disabled unless a controlled egress proxy is configured; the proxy must independently enforce connection-time destination validation. S3 snapshot objects are stored under per-user prefixes with server-side encryption and must remain private.

Per-account ntfy topics are HMAC-derived. Public ntfy topics act as bearer capabilities: do not disclose topic names or send credentials, tokens, private source code or other sensitive data in notification messages.

## Migrations and data preservation

Back up the database before deployment. Migration `0003_user_ownership` assigns existing unowned records to an inactive legacy account, preserving them without exposing them to new users. Migration `0004_data_integrity_and_indexes` retains only the most recent active focus session per account, adds a database constraint preventing multiple active sessions, and adds tenant query indexes. Migration `0005_renewal_notice_ledger` adds an idempotency ledger for daily renewal notifications.

Run migrations in order with `python manage.py migrate`. Reassign legacy records only through an explicit, audited administrative process after verifying ownership. Never reassign them automatically to the first user who signs in.

## Testing and CI

GitHub Actions runs Django checks, migration drift checks, migrations and backend security tests against PostgreSQL, plus frontend auth regression tests, ESLint and a Next.js production build. CI uses placeholder Clerk settings and non-production database credentials.

## Infrastructure and subscriptions

Domain assets, DNS state, hosting services, AI subscriptions, renewal summaries and the `check_renewals` management command from `feature/infrastructure-subscriptions` are preserved and user-scoped. See `docs/INFRASTRUCTURE-SUBSCRIPTIONS.md`.

See `docs/OPERATIONS.md` for release, PostgreSQL backup, restore-drill, scheduler and incident-response procedures.\n\n## Operational limitations

- Hosting checks establish HTTP reachability, not provider billing or deployment health.
- DNS monitoring currently checks IPv4 A records only; MX, TXT, CNAME, NS and DNSSEC are not implemented.
- Renewal dates are user-managed; automatic registrar/RDAP and provider billing integrations are not implemented.
- Renewal notification delivery is at-least-once across process crashes: a crash after ntfy accepts a message but before the ledger is marked sent can cause a retry.
- The server-side repository scanner can inspect only filesystems mounted into the backend. Monitoring a customer's laptop requires a separately authenticated desktop agent; do not mount arbitrary customer directories into a shared production API container.
- Production operations require external backups, restore drills, centralized error tracking, metrics, and alerting.
