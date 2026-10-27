"""Tiny SQLite helper (standard library only).

Every query in the project uses `?` placeholders - never string formatting -
so user input can't turn into SQL (SQL injection).
"""

import os
import sqlite3
from contextlib import contextmanager

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS records (
    id                     TEXT PRIMARY KEY,
    owner_id               TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title                  TEXT NOT NULL,
    total_mutations        INTEGER NOT NULL,
    overall_classification TEXT NOT NULL,
    report_json            TEXT NOT NULL,
    created_at             TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_records_owner ON records(owner_id);
"""


@contextmanager
def get_connection():
    """Open a connection, commit on success, roll back on error, always close.

    The path is read from config at call time (tests point it at a temp file)
    and the schema is created if missing, so no separate "init" step is needed.
    """
    path = config.DATABASE_PATH
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
