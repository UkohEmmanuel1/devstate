import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
BASE_DIR=Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR/".env")
SECRET_KEY=os.environ["DJANGO_SECRET_KEY"]
DEBUG=os.getenv("DJANGO_DEBUG","false").lower()=="true"
ALLOWED_HOSTS=[x.strip() for x in os.getenv("DJANGO_ALLOWED_HOSTS","localhost,127.0.0.1").split(",") if x.strip()]
INSTALLED_APPS=["django.contrib.admin","django.contrib.auth","django.contrib.contenttypes","django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles","corsheaders","rest_framework","core"]
MIDDLEWARE=["django.middleware.security.SecurityMiddleware","corsheaders.middleware.CorsMiddleware","django.contrib.sessions.middleware.SessionMiddleware","django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware","django.contrib.messages.middleware.MessageMiddleware"]
ROOT_URLCONF="config.urls"
TEMPLATES=[{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[],"APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.debug","django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION="config.wsgi.application"
DATABASE_URL=os.getenv("DATABASE_URL")
DATABASES={"default":dj_database_url.parse(DATABASE_URL,conn_max_age=600,ssl_require=not DEBUG) if DATABASE_URL else {"ENGINE":"django.db.backends.sqlite3","NAME":BASE_DIR/"db.sqlite3"}}
LANGUAGE_CODE="en-us";TIME_ZONE="Africa/Lagos";USE_I18N=True;USE_TZ=True
STATIC_URL="static/";DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS=[x.strip() for x in os.getenv("CORS_ALLOWED_ORIGINS","http://localhost:3000").split(",") if x.strip()]
CSRF_TRUSTED_ORIGINS=[x.strip() for x in os.getenv("CSRF_TRUSTED_ORIGINS","").split(",") if x.strip()]
CLERK_ISSUER=os.environ["CLERK_ISSUER"].rstrip("/")+"/"
CLERK_JWKS_URL=os.environ["CLERK_JWKS_URL"]
CLERK_AUDIENCE=os.getenv("CLERK_AUDIENCE","")
CLERK_AUTHORIZED_PARTIES=[x.strip() for x in os.getenv("CLERK_AUTHORIZED_PARTIES","").split(",") if x.strip()]
REST_FRAMEWORK={"DEFAULT_AUTHENTICATION_CLASSES":["core.authentication.ClerkJWTAuthentication"],"DEFAULT_PERMISSION_CLASSES":["rest_framework.permissions.IsAuthenticated"],"DEFAULT_RENDERER_CLASSES":["rest_framework.renderers.JSONRenderer"]}
NTFY_SERVER=os.getenv("DEVSTATE_NTFY_SERVER","https://ntfy.sh").rstrip("/")
NTFY_TOPIC_PREFIX=os.getenv("DEVSTATE_NTFY_TOPIC_PREFIX","")
NTFY_TOPIC_SECRET=os.getenv("DEVSTATE_NTFY_TOPIC_SECRET","")
NTFY_TOKEN=os.getenv("DEVSTATE_NTFY_TOKEN","")
SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO","https")
SESSION_COOKIE_SECURE=not DEBUG;CSRF_COOKIE_SECURE=not DEBUG
SECURE_SSL_REDIRECT=os.getenv("SECURE_SSL_REDIRECT","false").lower()=="true"
SECURE_HSTS_SECONDS=int(os.getenv("SECURE_HSTS_SECONDS","0" if DEBUG else "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS=not DEBUG;SECURE_HSTS_PRELOAD=not DEBUG
