"""
app/core/security.py — JWT tokens and password hashing.

WHY SEPARATE FROM config.py:
  config.py is about reading settings. security.py is about cryptographic
  operations. Mixing them makes both harder to test.

JWT STRATEGY:
  Access token  — short-lived (30 min), stored in memory on the frontend.
  Refresh token — long-lived (7 days), stored in an httpOnly cookie.

  This combination means:
    - XSS can't steal the refresh token (httpOnly blocks JS access).
    - CSRF can't use the refresh token (the endpoint only accepts JSON, not forms).
    - If an access token is stolen, it expires in 30 minutes.
    - Users stay logged in across tab closes (the cookie persists).

TOKEN CLAIMS:
  {"sub": "<user_id>", "type": "access"|"refresh", "exp": <unix timestamp>}
  "sub" = subject — standard JWT claim for "who this token is about".
  "type" distinguishes access from refresh so a refresh token can't be
  used as an access token even if somehow leaked.

PASSLIB:
  bcrypt with 12 rounds. Strong enough to make brute force impractical,
  fast enough not to add noticeable latency to login.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt as _bcrypt
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, InvalidTokenError, TokenExpiredError
from app.db.session import get_db

settings = get_settings()

# ── Password hashing ─────────────────────────────────────────────────────────
# bcrypt 4+ enforces the 72-byte limit at the C level and can't be suppressed
# via passlib flags. We bypass passlib entirely and call bcrypt directly,
# pre-hashing the password to a 32-byte SHA-256 digest first.
# 32 bytes is always under 72, so the limit is never hit regardless of
# how long the user's password is.

def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt. One-way, not reversible."""
    digest = hashlib.sha256(plain.encode("utf-8")).digest()  # always 32 bytes
    return _bcrypt.hashpw(digest, _bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash."""
    digest = hashlib.sha256(plain.encode("utf-8")).digest()
    return _bcrypt.checkpw(digest, hashed.encode("utf-8"))


# ── Token creation ────────────────────────────────────────────────────────────

def create_access_token(user_id: uuid.UUID) -> str:
    """
    Create a short-lived JWT access token.

    Signed with HMAC-SHA256 using the secret key from settings.
    The frontend stores this in memory (not localStorage) to block XSS.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """
    Create a long-lived JWT refresh token.

    Stored in an httpOnly cookie — never readable by JavaScript.
    Used only to issue new access tokens via /auth/refresh.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


# ── Token verification ────────────────────────────────────────────────────────

def _decode_token(token: str, expected_type: str) -> uuid.UUID:
    """
    Decode and validate a JWT. Returns the user_id (sub claim).
    Raises typed auth exceptions (mapped to HTTP 401 in exception handlers).
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except JWTError:
        raise InvalidTokenError()

    token_type = payload.get("type")
    if token_type != expected_type:
        raise InvalidTokenError()

    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError()

    try:
        return uuid.UUID(sub)
    except ValueError:
        raise InvalidTokenError()


def decode_access_token(token: str) -> uuid.UUID:
    """Validate an access token and return the user_id."""
    return _decode_token(token, "access")


def decode_refresh_token(token: str) -> uuid.UUID:
    """Validate a refresh token and return the user_id."""
    return _decode_token(token, "refresh")


# ── FastAPI dependencies ──────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> uuid.UUID:
    """
    FastAPI dependency: extract and validate the Bearer token.

    Usage in route handlers:
        @router.get("/me")
        async def me(user_id: UUID = Depends(get_current_user_id)):
            ...

    Returns the user_id UUID.
    Raises AuthenticationError (→ HTTP 401) if token is missing/invalid/expired.
    """
    if credentials is None:
        raise AuthenticationError("No authentication token provided.")
    return decode_access_token(credentials.credentials)


async def get_current_user(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    FastAPI dependency: resolve user_id to a User ORM object.

    Usage when you need the full User record:
        @router.get("/profile")
        async def profile(user = Depends(get_current_user)):
            return user.display_name
    """
    from app.db.repositories.user_repo import user_repo
    from app.core.exceptions import NotFoundError

    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return user
