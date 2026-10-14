"""Passwords and login tokens.

Security-critical file: change it only with tests, and get a review from HP.
- Passwords are hashed with Argon2id and never stored or logged as plain text.
- Access tokens are signed JWTs that expire after ACCESS_TOKEN_MINUTES.
- Refresh tokens are long random strings. The database stores only their SHA-256 hash.
"""

import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

ACCESS_TOKEN_MINUTES = 15
REFRESH_TOKEN_DAYS = 30
JWT_ALGORITHM = "HS256"
MIN_SECRET_LENGTH = 32

# Argon2id with the library's recommended settings.
_hasher = PasswordHasher()


# --- Passwords ---


def hash_password(password: str) -> str:
    """Turn a password into a one-way hash for the database."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """True only if the password matches the stored hash. Never raises."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


# Used when the email does not exist, so a failed login takes the same time either way.
# Otherwise an attacker could measure response times to find out which emails are registered.
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing")


def burn_time_like_a_password_check() -> None:
    verify_password("wrong-password", _DUMMY_HASH)


# --- Access tokens (short-lived, signed) ---


def _jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET", "")
    if len(secret) < MIN_SECRET_LENGTH:
        raise RuntimeError(f"JWT_SECRET must be set in .env and be at least {MIN_SECRET_LENGTH} characters long.")
    return secret


def create_access_token(user_id: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def read_access_token(token: str) -> int | None:
    """Return the user id if the token is valid and not expired, otherwise None."""
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=[JWT_ALGORITHM],  # only accept our algorithm, never "none"
            options={"require": ["exp", "iat", "sub", "type"]},
        )
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    try:
        return int(payload["sub"])
    except (TypeError, ValueError):
        return None


# --- Refresh tokens (long-lived, random, stored only as a hash) ---


def new_refresh_token() -> tuple[str, str]:
    """Return (token for the app, hash for the database)."""
    token = secrets.token_urlsafe(32)
    return token, hash_refresh_token(token)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_token_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_DAYS)
