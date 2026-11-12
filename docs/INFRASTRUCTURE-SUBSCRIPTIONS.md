# Infrastructure and subscription tracking

DevState can now store and inspect domains, hosting services and AI subscriptions.

## API

- `GET/POST /api/domains/`, `GET/PATCH/DELETE /api/domains/{id}/`
- `POST /api/domains/{id}/check_dns/` checks IPv4 A-record resolution against configured expected A records.
- `GET/POST /api/hosting/`, `GET/PATCH/DELETE /api/hosting/{id}/`
- `POST /api/hosting/{id}/check/` performs an HTTP(S) reachability check.
- `GET/POST /api/ai-subscriptions/`, `GET/PATCH/DELETE /api/ai-subscriptions/{id}/`
- `GET /api/renewals/` lists upcoming domain, hosting and AI subscription renewal dates.
- `POST /api/infrastructure/check/` checks all saved domain A records and hosting URLs.

## What the checks mean

DNS checks verify that a domain resolves to IPv4 addresses and can flag a mismatch against expected A records. This first version does not yet inspect MX, TXT, CNAME, NS or DNSSEC records. Hosting checks verify HTTP reachability and record the response status; they do not inspect provider-side billing, deployment state or resource usage.

AI subscription renewal dates and prices are user-entered. Providers generally do not expose a universal API for reading a person's subscription and billing data, so DevState does not claim to discover account billing automatically.

## Apply migrations

From `backend/`:

```powershell
python manage.py migrate
```

These endpoints are intended for local development. Do not expose the unauthenticated API publicly.
