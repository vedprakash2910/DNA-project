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
