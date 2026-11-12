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
Schedule `python manage.py check_renewals` daily. The command creates owner-scoped events and sends to per-account HMAC-derived ntfy topics. Configure `DEVSTATE_NTFY_TOPIC_PREFIX` and a high-entropy `DEVSTATE_NTFY_TOPIC_SECRET`; optional server auth token is `DEVSTATE_NTFY_TOKEN`. Public ntfy topics are bearer capabilities: never publish topic names or include credentials/secrets in messages.

## Check limitations
DNS currently verifies IPv4 A records. MX, TXT, CNAME, NS and DNSSEC are not implemented. Hosting checks verify HTTP reachability, not provider billing or deployment state. Expiry and renewal dates are entered manually; automatic registrar/RDAP and provider billing integrations remain future work.

## Migration
Back up the database and run `python manage.py migrate`. Existing records are assigned to an inactive legacy account to preserve them without exposing them to new users. Any reassignment requires an explicit, audited administrative action.
