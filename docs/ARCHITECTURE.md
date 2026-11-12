# DevState architecture

## Runtime components

- **Next.js 16 frontend** (`frontend/`): public landing page, Clerk sign-in/sign-up, protected dashboard and infrastructure screens. `proxy.ts` performs early route protection; server layouts repeat the authorization check. The browser calls only the same-origin `/api/backend/*` route.
- **Next.js API proxy** (`frontend/src/app/api/backend/[...path]/route.ts`): requires a Clerk session, obtains a session token server-side, validates path containment, caps request bodies and forwards the bearer token to the private Django API.
- **Clerk**: identity provider and session issuer. It is not the application's data store.
- **Django REST Framework** (`backend/`): validates Clerk RS256 JWTs against cached JWKS, maps verified `sub` values to local users, enforces per-user querysets and contains business logic.
- **PostgreSQL**: production source of truth for users, events, focus sessions, repositories, domains, hosting services, AI subscriptions and renewal-notice state. SQLite is for local development only.
- **Private S3-compatible storage**: production recovery snapshots, stored below a per-user key prefix.
- **Controlled egress proxy**: production outbound hosting checks. It must validate the resolved destination at connection time and block internal/metadata ranges.
- **ntfy**: phone notifications sent to HMAC-derived per-account topics.
- **Sentry (optional)**: backend error tracking with default PII disabled and request-body/auth-header scrubbing.

## Request flow

1. A user signs in through Clerk.
2. Next.js middleware protects application routes.
3. Client-side dashboard requests go to the same-origin backend proxy.
4. The proxy obtains the current Clerk session token on the server and forwards it as a Bearer token.
5. Django resolves a signing key from cached Clerk JWKS and validates algorithm, signature, issuer, time claims, subject, optional audience and configured authorized party.
6. Django maps the verified Clerk subject to a local user. Request-supplied user IDs are never used to determine ownership.
7. DRF views filter user-owned records by `request.user`; create operations assign the owner server-side.
8. Database uniqueness constraints provide a second line of defense for per-user project paths, domain names and active focus sessions.

## Trust boundaries

- Browser input is untrusted, including URL path segments and request bodies.
- Clerk session tokens are accepted only after server-side signature and claim validation.
- The Django service should not be directly exposed to the public internet; the Next.js proxy should use its private network address.
- `X-Forwarded-Proto` must be set by a trusted reverse proxy that removes client-supplied forwarding headers.
- Production outbound requests must pass through an egress proxy that enforces connection-time destination policy. The API's preliminary DNS lookup is not sufficient by itself to prevent DNS rebinding.
- S3 snapshot storage must be private; access is through backend credentials/IAM, not public object URLs.
- ntfy topic names are bearer capabilities and must not be written to logs or shared.
- Error telemetry must not contain bearer tokens, cookies, request bodies or provider secrets.

## Data and background work

Django is the system of record. The `check_renewals` management command is scheduled once daily by the deployment platform. A database-backed `RenewalNotice` row serializes concurrent attempts and records retry state. Notification delivery is at-least-once if the process crashes after ntfy accepts a message but before the row is marked sent.

Repository scanning is enabled only in local DEBUG mode and is disabled in production because untrusted Git repositories can trigger configured Git helpers/filters. A separately authenticated desktop agent with an explicit repository allowlist is required for customer-device monitoring.

## Legacy Python package

`src/devstate/` contains an earlier standalone Python event router, SQLite persistence and notifier. It is not imported by the Django web runtime and is not the web application's source of truth. Keep it isolated until it has a separately defined SDK/agent contract and its own dependency manifest and CI job; do not add new duplicate business logic there.
