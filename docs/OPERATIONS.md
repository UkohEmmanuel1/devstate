# DevState production operations

This runbook assumes PostgreSQL, private S3-compatible snapshot storage, HTTPS termination, a controlled egress proxy and a configured Clerk production instance.

## Release procedure

1. Take and verify a database backup.
2. Deploy the backend image and configuration.
3. Run `python manage.py check --deploy`.
4. Run `python manage.py migrate --noinput` once as a release step.
5. Run `python manage.py collectstatic --noinput` (the container entrypoint also collects static assets).
6. Deploy the frontend with the server-only Clerk secret and private backend URL.
7. Verify the health endpoint, sign-in, unauthenticated API rejection, tenant isolation and infrastructure/subscription CRUD.
8. Enable customer traffic only after the verification checklist succeeds.

Do not run migrations concurrently from every web worker.

## PostgreSQL backup

Use the hosting provider's automated point-in-time recovery and scheduled backups where available. For an additional logical backup, run from a secured operations environment with PostgreSQL client tools installed:

```bash
umask 077
mkdir -p ./private-backups
pg_dump --format=custom --no-owner "$DATABASE_URL" \
  --file "./private-backups/devstate-$(date -u +%Y%m%dT%H%M%SZ).dump"
```

Encrypt backups before copying them off the trusted operations host. Restrict access, define retention and verify backup completion alerts.

## Restore drill

Restore into a new, isolated PostgreSQL database first. Do not test restoration against the live production database.

```bash
createdb devstate_restore_drill
pg_restore --no-owner --dbname "$RESTORE_DATABASE_URL" ./private-backups/backup.dump
```

After restoration, run Django checks, migration status, tenant-isolation smoke tests and application read checks. Record the recovery point and elapsed recovery time. A backup that has never been restored is not a verified recovery plan.

## Scheduled renewal reminders

Run `python manage.py check_renewals` once daily using the platform scheduler or a dedicated scheduler service. Monitor process exit status and logs. The `RenewalNotice` ledger prevents duplicate concurrent daily work and retries pending notifications. Delivery is at-least-once across a process crash after provider acceptance.

## Monitoring and incident response

- Configure `SENTRY_DSN` and set `SENTRY_ENVIRONMENT`; default PII capture is disabled.
- Collect application logs from stdout/stderr centrally. Do not log bearer tokens, Clerk secrets, ntfy topic names or database credentials.
- Alert on sustained 5xx responses, database connection failures, elevated auth failures, scheduler failures and snapshot storage errors.
- Track database capacity, connection saturation, query latency, object-storage failures and egress-proxy denials.
- Keep a tested rollback image for the frontend and backend. Schema changes must remain backward-compatible with the previous application version during rollout.
- Rotate Clerk secrets, Django secret, ntfy tokens, database credentials and egress-proxy credentials through the hosting provider's secret manager.

## Recovery and data ownership

Migration `0003_user_ownership` moves pre-auth records to an inactive legacy account. Do not reactivate or bulk-assign those records without verified ownership and an audited operator action. Migration `0004` consolidates multiple active focus sessions per user before enforcing the database uniqueness constraint. Migration `0005` introduces the renewal idempotency ledger.
