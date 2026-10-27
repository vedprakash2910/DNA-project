"""Password hashing and JWT helpers.

Pure Python (no FastAPI) so it can be unit-tested on its own.

PASSWORDS  -> scrypt (memory-hard, in the standard library) with a random salt.
              We never store or log the password itself.
TOKENS     -> JWT signed with HS256 (HMAC-SHA256) using config.JWT_SECRET.
"""

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

import config
from utils.exceptions import TokenExpiredError, TokenInvalidError

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
# scrypt cost. The values are stored INSIDE every hash, so you can raise them
# later and old hashes still verify.
SCRYPT_N = 2 ** 15   # CPU/memory cost
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
KEY_BYTES = 32


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        maxmem=256 * n * r,   # hashlib's default limit (32 MiB) is too small for n=2**15
        dklen=KEY_BYTES,
    )


def hash_password(password: str) -> str:
    """Return 'scrypt$N$r$p$<salt>$<hash>'. A new random salt is used every time."""
    salt = os.urandom(SALT_BYTES)
    digest = _scrypt(password, salt, SCRYPT_N, SCRYPT_R, SCRYPT_P)
    return "$".join([
        "scrypt", str(SCRYPT_N), str(SCRYPT_R), str(SCRYPT_P),
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    ])


def verify_password(password: str, stored_hash: str) -> bool:
    """True if `password` matches `stored_hash`. Never raises on a bad hash string."""
    try:
        scheme, n, r, p, salt_b64, digest_b64 = stored_hash.split("$")
        if scheme != "scrypt":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = _scrypt(password, salt, int(n), int(r), int(p))
    except (ValueError, TypeError):
        return False
    # constant-time comparison (a plain == can leak how many bytes matched)
    return hmac.compare_digest(actual, expected)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
def create_access_token(
    user_id: str,
    role: str,
    *,
    now: datetime | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Issue a signed token.

    Payload (the "claims"):
        sub   subject  = the user's id
        role  the user's role when the token was issued
        type  "access" (so other kinds of token can't be used by mistake)
        iat   issued-at time
        exp   expiry time - after this the token is rejected
    """
    issued_at = now or datetime.now(timezone.utc)
    lifetime = expires_delta if expires_delta is not None else timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": issued_at,
        "exp": issued_at + lifetime,
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Verify signature + expiry and return the payload.

    Raises TokenExpiredError (401 token_expired) or TokenInvalidError (401 invalid_token).
    """
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            # Always name the allowed algorithm(s): this blocks "alg: none"
            # tokens and algorithm-swapping tricks.
            algorithms=[config.JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Access token has expired. Please log in again.") from None
    except jwt.InvalidTokenError:
        raise TokenInvalidError("Invalid access token.") from None

    if payload.get("type") != "access":
        raise TokenInvalidError("Invalid access token.")

    return payload
