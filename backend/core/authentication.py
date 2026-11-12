"""Clerk session JWT authentication for Django REST Framework."""
import hashlib
import logging
import threading

import jwt
from jwt import PyJWKClient
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import ClerkProfile

logger = logging.getLogger(__name__)
_jwks = None
_jwks_lock = threading.Lock()


def jwks_client():
    """Return a process-local, cached Clerk JWKS client."""
    global _jwks
    if _jwks is None:
        with _jwks_lock:
            if _jwks is None:
                _jwks = PyJWKClient(
                    settings.CLERK_JWKS_URL,
                    cache_jwk_set=True,
                    lifespan=3600,
                    timeout=5,
                )
    return _jwks


def _local_username(subject):
    # A fixed-length deterministic name avoids collisions from truncating long
    # Clerk subject values to Django's username field limit.
    digest = hashlib.sha256(subject.encode("utf-8")).hexdigest()
    return f"clerk_{digest}"


def _get_or_create_local_user(subject):
    User = get_user_model()
    try:
        with transaction.atomic():
            profile = ClerkProfile.objects.select_related("user").filter(
                clerk_user_id=subject
            ).first()
            if profile:
                return profile.user

            user, _ = User.objects.get_or_create(
                username=_local_username(subject),
                defaults={"is_active": True},
            )
            profile, _ = ClerkProfile.objects.get_or_create(
                clerk_user_id=subject,
                defaults={"user": user},
            )
            return profile.user
    except IntegrityError:
        # Another request may have provisioned the same Clerk subject between
        # the initial lookup and insert. Re-read after the failed transaction.
        try:
            return ClerkProfile.objects.select_related("user").get(
                clerk_user_id=subject
            ).user
        except ClerkProfile.DoesNotExist as exc:
            logger.exception("Concurrent Clerk profile provisioning failed")
            raise AuthenticationFailed("Unable to provision account.") from exc


class ClerkJWTAuthentication(BaseAuthentication):
    """Validate Clerk RS256 session tokens and map sub to a local user."""

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if len(parts) != 2 or parts[0].lower() != b"bearer":
            raise AuthenticationFailed("Use a Bearer session token.")

        try:
            token = parts[1].decode("ascii")
            signing_key = jwks_client().get_signing_key_from_jwt(token).key
            audience = settings.CLERK_AUDIENCE
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                issuer=settings.CLERK_ISSUER,
                audience=audience or None,
                options={
                    "verify_aud": bool(audience),
                    "require": ["exp", "iat", "sub"],
                },
                leeway=30,
            )
            subject = claims.get("sub")
            if not isinstance(subject, str) or not subject.strip():
                raise AuthenticationFailed("Token subject is missing.")

            allowed_parties = settings.CLERK_AUTHORIZED_PARTIES
            if allowed_parties:
                authorized_party = claims.get("azp")
                if not authorized_party or authorized_party not in allowed_parties:
                    raise AuthenticationFailed("Untrusted or missing token origin.")
        except AuthenticationFailed:
            raise
        except (jwt.PyJWTError, UnicodeDecodeError, ValueError, TypeError) as exc:
            logger.info("Rejected invalid Clerk session token: %s", type(exc).__name__)
            raise AuthenticationFailed("Invalid or expired Clerk token.") from exc
        except Exception as exc:
            # JWKS transport, timeout and key-rotation failures must fail closed.
            logger.warning("Clerk JWKS verification unavailable: %s", type(exc).__name__)
            raise AuthenticationFailed("Unable to verify Clerk session.") from exc

        user = _get_or_create_local_user(subject)
        if not user.is_active:
            raise AuthenticationFailed("Account disabled.")
        return user, claims

    def authenticate_header(self, request):
        return "Bearer"
