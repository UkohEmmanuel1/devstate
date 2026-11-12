# Django API

All API routes require a verified Clerk Bearer JWT except `GET /api/health/`. Django validates JWT signatures with Clerk JWKS and scopes every application queryset to the authenticated user.

```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py test
python manage.py runserver 127.0.0.1:8000
```

Set Clerk issuer/JWKS, Django secret, database and origin allowlists in `.env`. Use PostgreSQL through `DATABASE_URL` in production. Never commit `.env` or secrets.
