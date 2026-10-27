"""Registration and login logic. Pure Python (no FastAPI)."""

import logging
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from utils import security
from utils.database import get_connection
from utils.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError

logger = logging.getLogger(__name__)

_dummy_hash = None


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _public_user(row) -> dict:
    """Never include password_hash in anything that leaves this module."""
    return {
        "id": row["id"],
        "email": row["email"],
        "role": row["role"],
        "created_at": row["created_at"],
    }


def register_user(email: str, password: str) -> dict:
    """Create an account. The role is ALWAYS 'user' - clients can't pick it."""
    email = normalize_email(email)
    user_id = str(uuid4())
    password_hash = security.hash_password(password)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (id, email, password_hash, role, created_at) "
                "VALUES (?, ?, ?, 'user', ?)",
                (user_id, email, password_hash, created_at),
            )
    except sqlite3.IntegrityError:
        # The UNIQUE constraint on email is what really prevents duplicates
        # (a "check then insert" would be racy).
        raise EmailAlreadyRegisteredError(
            "An account with this email already exists"
        ) from None

    logger.info("User registered id=%s", user_id)
    return {"id": user_id, "email": email, "role": "user", "created_at": created_at}


def _get_dummy_hash() -> str:
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = security.hash_password("not-a-real-password")
    return _dummy_hash


def authenticate_user(email: str, password: str) -> dict:
    """Check email + password. Same error whichever one is wrong."""
    email = normalize_email(email)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if row is None:
        # Do the same amount of hashing work so response time doesn't reveal
        # whether the email exists.
        security.verify_password(password, _get_dummy_hash())
        logger.warning("Failed login attempt")
        raise InvalidCredentialsError("Invalid email or password")

    if not security.verify_password(password, row["password_hash"]):
        logger.warning("Failed login attempt user_id=%s", row["id"])
        raise InvalidCredentialsError("Invalid email or password")

    return _public_user(row)


def get_user_by_id(user_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _public_user(row) if row else None
