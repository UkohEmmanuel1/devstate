import jwt
from jwt import PyJWKClient
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from .models import ClerkProfile

_jwks = None
def jwks_client():
    global _jwks
    if _jwks is None:
        _jwks = PyJWKClient(settings.CLERK_JWKS_URL, cache_jwk_set=True, lifespan=3600, timeout=5)
    return _jwks

class ClerkJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts: return None
        if len(parts) != 2 or parts[0].lower() != b"bearer":
            raise AuthenticationFailed("Use a Bearer session token.")
        try:
            key = jwks_client().get_signing_key_from_jwt(parts[1].decode()).key
            audience = settings.CLERK_AUDIENCE
            claims = jwt.decode(parts[1], key, algorithms=["RS256"], issuer=settings.CLERK_ISSUER,
                audience=audience or None, options={"verify_aud": bool(audience), "require": ["exp", "iat", "sub"]}, leeway=30)
            if settings.CLERK_AUTHORIZED_PARTIES and claims.get("azp") and claims["azp"] not in settings.CLERK_AUTHORIZED_PARTIES:
                raise AuthenticationFailed("Untrusted token origin.")
            subject = claims["sub"]
        except AuthenticationFailed:
            raise
        except Exception as exc:
            raise AuthenticationFailed("Invalid or expired Clerk token.") from exc
        User = get_user_model()
        try:
            profile = ClerkProfile.objects.select_related("user").get(clerk_user_id=subject)
            user = profile.user
        except ClerkProfile.DoesNotExist:
            user, _ = User.objects.get_or_create(username=("clerk_" + subject)[:150], defaults={"is_active": True})
            ClerkProfile.objects.create(user=user, clerk_user_id=subject)
        if not user.is_active: raise AuthenticationFailed("Account disabled.")
        return user, claims
    def authenticate_header(self, request): return "Bearer"
