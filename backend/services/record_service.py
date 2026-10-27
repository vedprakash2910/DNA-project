"""Saved analysis records + the rules about who may see them.

AUTHORIZATION lives here: `get_authorized_record` is the single place that
decides "may this user touch this record?" (owner, or admin).
Pure Python (no FastAPI).
"""

import json
from datetime import datetime, timezone
from uuid import uuid4

from utils.database import get_connection
from utils.exceptions import ForbiddenError, RecordNotFoundError


def _summary(row) -> dict:
    return {
        "id": row["id"],
        "owner_id": row["owner_id"],
        "title": row["title"],
        "created_at": row["created_at"],
        "total_mutations": row["total_mutations"],
        "overall_classification": row["overall_classification"],
    }


def can_access(record_owner_id: str, user: dict) -> bool:
    return user["role"] == "admin" or record_owner_id == user["id"]


def create_record(owner_id: str, title: str, report: dict) -> dict:
    record_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    summary = report["summary"]

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO records (id, owner_id, title, total_mutations, "
            "overall_classification, report_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                record_id, owner_id, title,
                summary["total_mutations"], summary["overall_classification"],
                json.dumps(report), created_at,
            ),
        )
    return {
        "id": record_id, "owner_id": owner_id, "title": title, "created_at": created_at,
        "total_mutations": summary["total_mutations"],
        "overall_classification": summary["overall_classification"],
        "report": report,
    }


def list_records(user: dict) -> list[dict]:
    """A normal user sees only their own records; an admin sees all."""
    with get_connection() as conn:
        if user["role"] == "admin":
            rows = conn.execute("SELECT * FROM records ORDER BY created_at DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM records WHERE owner_id = ? ORDER BY created_at DESC",
                (user["id"],),
            ).fetchall()
    return [_summary(row) for row in rows]


def _fetch(record_id: str):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()


def get_authorized_record(record_id: str, user: dict) -> dict:
    """404 if it doesn't exist, 403 if it belongs to someone else (unless admin)."""
    row = _fetch(record_id)
    if row is None:
        raise RecordNotFoundError("Record not found")
    if not can_access(row["owner_id"], user):
        raise ForbiddenError("You do not have permission to access this record")
    return {**_summary(row), "report": json.loads(row["report_json"])}


def delete_record(record_id: str, user: dict) -> None:
    get_authorized_record(record_id, user)  # raises 404 / 403
    with get_connection() as conn:
        conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
