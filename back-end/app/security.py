"""Password hashing (argon2id) and stateless access tokens (JWT, HS256)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from .errors import ApiError

_hasher = PasswordHasher()
# Verified when the email is unknown so both login failures take the same time.
_DUMMY_HASH = _hasher.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


class TokenService:
    ALGORITHM = "HS256"

    def __init__(self, secret: str, ttl: timedelta):
        self._secret, self._ttl = secret, ttl

    def issue(self, user_id: int, now: datetime | None = None) -> str:
        issued = now or datetime.now(timezone.utc)
        claims = {"sub": str(user_id), "iat": issued, "exp": issued + self._ttl}
        return jwt.encode(claims, self._secret, algorithm=self.ALGORITHM)

    def verify(self, token: str) -> int:
        """Return the user id, or raise a 401 ApiError."""
        try:
            claims = jwt.decode(
                token, self._secret, algorithms=[self.ALGORITHM], options={"require": ["sub", "exp", "iat"]}
            )
            return int(claims["sub"])
        except jwt.ExpiredSignatureError:
            raise ApiError("Your session has expired. Please sign in again.", 401, "invalid_token") from None
        except (jwt.InvalidTokenError, ValueError):
            raise ApiError("Invalid access token.", 401, "invalid_token") from None
