# Infrastructure and subscription tracking

DevState stores and inspects domains, hosting services and AI subscriptions.

## API

- `GET/POST /api/domains/`, `GET/PATCH/DELETE /api/domains/{id}/`
- `POST /api/domains/{id}/check_dns/` checks IPv4 A-record resolution against configured expected A records.
- `GET/POST /api/hosting/`, `GET/PATCH/DELETE /api/hosting/{id}/`
- `POST /api/hosting/{id}/check/` performs an HTTP(S) reachability check.
- `GET/POST /api/ai-subscriptions/`, `GET/PATCH/DELETE /api/ai-subscriptions/{id}/`
- `GET /api/renewals/` lists upcoming domain, hosting and AI subscription renewal dates.
- `POST /api/infrastructure/check/` checks all saved domain A records and hosting URLs.

## Renewal notifications

AI subscription renewal dates/prices are entered manually. Run this command daily to create priority events and send ntfy push notifications for upcoming renewals:

```powershell
cd backend
python manage.py check_renewals
```

For automatic daily execution on Windows, create a Task Scheduler task that runs `python.exe` with argument `manage.py check_renewals`, and set its working directory to the repository's `backend` folder. Use the Python executable inside `.venv\\Scripts\\python.exe`. The command logs at most one alert per asset per local calendar day.

## What the checks mean

DNS checks currently verify IPv4 A-record resolution and can flag mismatches against configured expected A records. MX, TXT, CNAME, NS and DNSSEC checks are not implemented yet. Hosting checks verify HTTP reachability and record the response status; they do not inspect provider-side billing, deployment state or resource usage.

Domain expiration and AI/hosting renewal dates are currently supplied by the user. Automatic registrar/RDAP expiry discovery and provider billing integrations are future work. Most AI providers do not expose a universal API for reading a person's billing subscription.

## Apply migrations

From `backend/`:

```powershell
python manage.py migrate
```

These endpoints are intended for local development. Do not expose the unauthenticated API publicly.
