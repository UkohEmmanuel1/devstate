import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be configured.")

ALLOWED_HOSTS = [
    value.strip()
    for value in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if value.strip()
]
DATABASE_URL = os.getenv("DATABASE_URL")
if not DEBUG:
    if not DATABASE_URL:
        raise ImproperlyConfigured("DATABASE_URL must be configured outside DEBUG mode.")
    if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
        raise ImproperlyConfigured("Production DJANGO_ALLOWED_HOSTS must be explicit; wildcards are forbidden.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "core",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG)
    if DATABASE_URL
    else {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
    value.strip()
    for value in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if value.strip()
]
CSRF_TRUSTED_ORIGINS = [
    value.strip()
    for value in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if value.strip()
]
if not DEBUG and (not CORS_ALLOWED_ORIGINS or not CSRF_TRUSTED_ORIGINS):
    raise ImproperlyConfigured("Production CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS must be explicit.")

CLERK_ISSUER = os.environ.get("CLERK_ISSUER", "").rstrip("/")
CLERK_JWKS_URL = os.environ.get("CLERK_JWKS_URL", "")
if not CLERK_ISSUER or not CLERK_JWKS_URL:
    raise ImproperlyConfigured("CLERK_ISSUER and CLERK_JWKS_URL must be configured.")
CLERK_AUDIENCE = os.getenv("CLERK_AUDIENCE", "")
CLERK_AUTHORIZED_PARTIES = [
    value.strip()
    for value in os.getenv("CLERK_AUTHORIZED_PARTIES", "").split(",")
    if value.strip()
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["core.authentication.ClerkJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("API_ANON_RATE", "20/min"),
        "user": os.getenv("API_USER_RATE", "300/min"),
        "project_scan": os.getenv("API_PROJECT_SCAN_RATE", "6/min"),
        "snapshots": os.getenv("API_SNAPSHOT_RATE", "5/hour"),
        "notifications": os.getenv("API_NOTIFICATION_RATE", "5/min"),
        "infrastructure_checks": os.getenv("API_INFRASTRUCTURE_CHECK_RATE", "10/min"),
    },
}

NTFY_SERVER = os.getenv("DEVSTATE_NTFY_SERVER", "https://ntfy.sh").rstrip("/")
NTFY_TOPIC_PREFIX = os.getenv("DEVSTATE_NTFY_TOPIC_PREFIX", "")
NTFY_TOPIC_SECRET = os.getenv("DEVSTATE_NTFY_TOPIC_SECRET", "")
NTFY_TOKEN = os.getenv("DEVSTATE_NTFY_TOKEN", "")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "false" if DEBUG else "true").lower() == "true"
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0" if DEBUG else "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
if not DEBUG and not SECURE_SSL_REDIRECT:
    raise ImproperlyConfigured("SECURE_SSL_REDIRECT must be enabled outside DEBUG mode.")

# Server-side monitoring must use a controlled proxy in production. The proxy
# must enforce destination-IP policy at connection time (including redirects).
DEVSTATE_EGRESS_PROXY_URL = os.getenv("DEVSTATE_EGRESS_PROXY_URL", "")

# Production recovery exports are stored in a private S3-compatible bucket.
DEVSTATE_SNAPSHOT_BUCKET = os.getenv("DEVSTATE_SNAPSHOT_BUCKET", "")
DEVSTATE_SNAPSHOT_REGION = os.getenv("DEVSTATE_SNAPSHOT_REGION", "")
DEVSTATE_SNAPSHOT_ENDPOINT = os.getenv("DEVSTATE_SNAPSHOT_ENDPOINT", "")


# Optional server-side error tracking. Never enable PII capture by default.
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    def scrub_sentry_event(event, hint):
        request = event.get("request", {})
        headers = request.get("headers", {})
        for header in list(headers):
            if header.lower() in {"authorization", "cookie", "set-cookie", "x-api-key"}:
                headers[header] = "[Filtered]"
        request.pop("data", None)
        return event

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.05")),
        send_default_pii=False,\n        before_send=scrub_sentry_event,
        environment=os.getenv(
            "SENTRY_ENVIRONMENT", "development" if DEBUG else "production"
        ),
    )
