import json
import time
import logging
from typing import Optional

import jwt
import requests
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import authentication, exceptions

logger = logging.getLogger(__name__)

_JWKS_CACHE = {
    "keys": None,
    "fetched_at": 0,
}


def _get_jwks() -> dict:
    jwks_url = getattr(settings, "NEON_AUTH_JWKS_URL", "")
    if not jwks_url:
        raise exceptions.AuthenticationFailed("Neon Auth JWKS URL is not configured")

    cache_ttl = getattr(settings, "NEON_AUTH_JWKS_CACHE_TTL", 300)
    now = int(time.time())
    if _JWKS_CACHE["keys"] and (now - _JWKS_CACHE["fetched_at"]) < cache_ttl:
        return _JWKS_CACHE["keys"]

    try:
        resp = requests.get(jwks_url, timeout=5)
        resp.raise_for_status()
        jwks = resp.json()
    except Exception as exc:
        logger.error("Failed to fetch Neon Auth JWKS: %s", exc)
        raise exceptions.AuthenticationFailed("Unable to fetch Neon Auth JWKS")

    _JWKS_CACHE["keys"] = jwks
    _JWKS_CACHE["fetched_at"] = now
    return jwks


def _get_public_key(token: str):
    try:
        header = jwt.get_unverified_header(token)
    except Exception:
        raise exceptions.AuthenticationFailed("Invalid token header")

    kid = header.get("kid")
    jwks = _get_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))

    raise exceptions.AuthenticationFailed("Signing key not found")


def _build_username(sub: Optional[str], email: Optional[str]) -> str:
    if sub:
        return f"neon_{sub}"
    if email:
        return f"neon_{email.split('@')[0]}"
    return "neon_user"


def _get_or_create_user(claims: dict) -> User:
    email = claims.get("email")
    sub = claims.get("sub")
    username = _build_username(sub, email)

    user = None
    if email:
        user = User.objects.filter(email=email).first()

    if not user:
        base_username = username[:150]
        candidate = base_username
        suffix = 1
        while User.objects.filter(username=candidate).exists():
            suffix += 1
            candidate = f"{base_username}_{suffix}"
            candidate = candidate[:150]
        user = User.objects.create_user(username=candidate, email=email or "")
        user.set_unusable_password()
        user.save(update_fields=["password"])

    return user


class NeonJWTAuthentication(authentication.BaseAuthentication):
    """Authenticate requests using Neon Auth JWTs (Bearer tokens)."""

    keyword = "Bearer"

    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).decode("utf-8")
        if not auth:
            return None

        parts = auth.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token = parts[1]
        public_key = _get_public_key(token)

        try:
            options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": bool(getattr(settings, "NEON_AUTH_AUDIENCE", "")),
            }
            claims = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=getattr(settings, "NEON_AUTH_AUDIENCE", None),
                issuer=getattr(settings, "NEON_AUTH_ISSUER", None),
                options=options,
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Invalid token")

        user = _get_or_create_user(claims)
        return (user, None)
