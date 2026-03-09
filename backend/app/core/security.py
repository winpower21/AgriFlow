"""
Security Utilities — JWT Tokens and Password Hashing
=====================================================

Provides the cryptographic primitives used by the auth layer:

- **JWT creation** (``create_access_token``):
  Encodes a payload dict into an HS256 JSON Web Token using ``python-jose``.
  The token includes an ``exp`` (expiration) claim derived from either an
  explicit ``expires_delta`` or the configured default from settings.

- **Password hashing** (``get_password_hash`` / ``verify_password``):
  Uses ``bcrypt`` for one-way hashing with an auto-generated salt.
  Passwords are encoded to UTF-8 before hashing/checking.

All secrets and algorithm settings are sourced from ``app.config.settings``
so they stay out of the code and can be rotated via environment variables.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.config import settings


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Generate a signed JWT access token.

    Args:
        data: Arbitrary claims to embed in the token payload.  The auth
              router typically passes ``{"user": user_id}`` here.
        expires_delta: Optional custom lifetime.  When ``None``, the token
                       expires after ``ACCESS_TOKEN_EXPIRE_MINUTES`` from
                       settings (default 60 min).

    Returns:
        A compact JWS string (``header.payload.signature``).
    """
    # Work on a copy so the caller's dict is not mutated
    to_encode = data.copy()

    # Compute the absolute expiration timestamp in UTC
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # ``exp`` is a registered JWT claim; python-jose validates it automatically
    # during ``jwt.decode`` and raises ExpiredSignatureError if past due.
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if the provided plaintext password matches the stored bcrypt hash.

    Both strings are encoded to UTF-8 bytes before comparison because
    ``bcrypt.checkpw`` operates on byte strings."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """Hash a plaintext password for storage using bcrypt.

    A new random salt is generated for every call, ensuring that identical
    passwords produce different hashes.  The returned string is a UTF-8
    decoded bcrypt hash suitable for storing in a text/varchar column.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")
