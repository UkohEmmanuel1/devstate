# Django API

All API routes require a verified Clerk Bearer JWT except `GET /api/health/`. Django validates RS256 JWT signatures with cached Clerk JWKS, validates issuer/time claims/audience and enforces the configured authorized-party allowlist. A local profile maps the verified Clerk subject to a Django user.

## Local development

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Configure DJANGO_DEBUG=true, Clerk issuer/JWKS and DJANGO_SECRET_KEY.
python manage.py migrate
python manage.py test
python manage.py runserver 127.0.0.1:8000
```

SQLite is supported for local development. Production requires PostgreSQL via `DATABASE_URL`, explicit host/CORS/CSRF allowlists, HTTPS redirect, a trusted reverse proxy, a controlled outbound egress proxy for hosting checks and private S3-compatible storage for recovery snapshots.

## Production

```bash
python manage.py check --deploy
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 30
```

Run migrations as a release step, not concurrently from every web worker. Configure daily `python manage.py check_renewals` through the platform scheduler. The notification ledger deduplicates daily reminders and retries pending deliveries; delivery is at-least-once if the process crashes after provider acceptance.

## Security

- DRF requires authentication by default; the health endpoint is explicitly public.
- Every user-owned queryset is scoped to `request.user`; owner fields are read-only and assigned server-side.
- The Clerk JWT verifier fails closed when JWKS verification fails. When `CLERK_AUTHORIZED_PARTIES` is configured, the token must contain a matching `azp`.
- Expensive project scanning, snapshots, notification and infrastructure-check operations have separate user throttles.
- Server-side repository scanning is disabled outside DEBUG mode until a separately authenticated desktop agent exists. Local scanning rejects symlinked roots, path escapes and external Git worktree metadata.
- Production hosting checks are disabled unless `DEVSTATE_EGRESS_PROXY_URL` is set. The proxy must enforce destination IP policy at connection time.
- Production snapshots require `DEVSTATE_SNAPSHOT_BUCKET` and are written to a per-user object prefix with server-side encryption.
- ntfy topics are HMAC-derived per account. Treat topic names as bearer capabilities and never put secrets in notification content.

## Data migrations

Back up PostgreSQL before deploying. Migration `0003_user_ownership` moves legacy unowned records to an inactive legacy account. Migration `0004_data_integrity_and_indexes` adds per-user active-focus uniqueness and query indexes. Migration `0005_renewal_notice_ledger` adds idempotency state for renewal reminders. Reassign legacy records only through an audited administrative procedure after verifying ownership.
