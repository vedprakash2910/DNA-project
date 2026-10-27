import os
APP_VERSION = "1.1.0"


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def _list_env(name: str, default: list[str]) -> list[str]:
    raw = os.environ.get(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


MAX_FILE_SIZE = _int_env("MAX_FILE_SIZE_BYTES", 5 * 1024 * 1024)  # 5 MB

MAX_SEQUENCE_LENGTH = _int_env("MAX_SEQUENCE_LENGTH", 1_000_000)

ALLOWED_ORIGINS = _list_env(
    "ALLOWED_ORIGINS",
    ["http://localhost:5173", "http://127.0.0.1:5173"],
)

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------
# Secret used to SIGN tokens. Set JWT_SECRET in the environment (>= 32 random
# characters). If it is missing we make a random one at start-up: fine for
# local development, but every restart (or extra worker) then invalidates
# all tokens, so main.py logs a warning.
_jwt_secret = os.environ.get("JWT_SECRET")
JWT_SECRET_IS_EPHEMERAL = not _jwt_secret
JWT_SECRET = _jwt_secret or secrets.token_urlsafe(48)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = _int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 30)

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# SQLite file holding users and saved records.
DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "app.db"),
)

