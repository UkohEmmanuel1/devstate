# Infrastructure and subscription tracking

DevState tracks domain assets, DNS state, hosting services and AI subscriptions inside each authenticated account. Every list/detail/update/delete operation is owner-scoped; another account's object ID returns 404.

## API

- `GET/POST /api/domains/`, `GET/PATCH/DELETE /api/domains/{id}/`
- `POST /api/domains/{id}/check_dns/` checks IPv4 A-record resolution.
- `GET/POST /api/hosting/`, `GET/PATCH/DELETE /api/hosting/{id}/`
- `POST /api/hosting/{id}/check/` performs HTTP(S) reachability check.
- `GET/POST /api/ai-subscriptions/`, `GET/PATCH/DELETE /api/ai-subscriptions/{id}/`
- `GET /api/renewals/` lists the signed-in account's renewal dates.
- `POST /api/infrastructure/check/` checks only the authenticated account's domains and hosting URLs.

## Renewal notifications

Schedule `python manage.py check_renewals` daily. A database-backed `RenewalNotice` ledger uses a unique per-owner/resource/renewal-date/reminder-day key to prevent concurrent duplicate daily sends. Failed or unconfigured deliveries remain pending for retry. A process crash after ntfy accepts a message but before the ledger is marked sent can still cause an at-least-once retry.

Configure `DEVSTATE_NTFY_TOPIC_PREFIX` and a high-entropy `DEVSTATE_NTFY_TOPIC_SECRET`; optional server auth token is `DEVSTATE_NTFY_TOKEN`. Public ntfy topics are bearer capabilities: never publish topic names or include credentials/secrets in messages.

## Monitoring and SSRF controls

DNS currently verifies IPv4 A records. MX, TXT, CNAME, NS and DNSSEC are not implemented. Hosting checks verify HTTP reachability, not provider billing or deployment state. Production checks require `DEVSTATE_EGRESS_PROXY_URL`; the proxy must independently resolve and validate destinations at connection time, block loopback/private/link-local/reserved/cloud-metadata ranges, and prevent redirect-based policy bypass. A preliminary application DNS lookup is defense in depth, not the connection-time security boundary.

Expiry and renewal dates are entered manually; automatic registrar/RDAP and provider billing integrations remain future work.

## Recovery snapshots

Development snapshots may be written to local `DEVSTATE_RECOVERY_DIR`. Production snapshots require a private S3-compatible bucket configured with `DEVSTATE_SNAPSHOT_BUCKET`; objects are stored under `snapshots/{user_id}/` and server-side encrypted. Keep the bucket private, apply lifecycle/retention rules and test restore procedures. The API does not expose public object URLs.

## Migration

Back up the database and run `python manage.py migrate`. Existing records are assigned to an inactive legacy account to preserve them without exposing them to new users. Migrations 0004 and 0005 add data-integrity constraints, indexes and renewal-notification idempotency. Any legacy reassignment requires an explicit, audited administrative action.
