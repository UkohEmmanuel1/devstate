# Dashboard

The public landing page is `/`; the Clerk-protected dashboard is `/dashboard` and infrastructure/subscription management is `/infrastructure`. Frontend requests use the same-origin `/api/backend/*` proxy. The server obtains the current Clerk session token and attaches it to Django; browser code does not handle Django credentials or trusted user IDs.

Configure `frontend/.env.local` and `backend/.env`; see the root README for Clerk setup, deployment and security.
