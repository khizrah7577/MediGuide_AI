"""
Optional SQLite assessment history.

History is OFF by default because this prototype does not provide
secure patient accounts. Anyone with access to the computer could
open the local database file.

Stored fields: timestamp, age, gender, symptoms, duration, severity,
language, urgency, summary, and the educational JSON.

Not stored: medications, existing conditions, additional notes.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.config import HISTORY_DB_PATH, ensure_data_dir
from src.utils import LOGGER, utc_now_iso

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS assessments (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    symptoms TEXT,
    duration TEXT,
    severity INTEGER,
    response_language TEXT,
    urgency_level TEXT,
    summary TEXT,
    result_json TEXT NOT NULL
)
"""


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else HISTORY_DB_PATH
    ensure_data_dir()
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path | None = None) -> None:
    with _connect(db_path) as connection:
        connection.execute(CREATE_SQL)
        connection.commit()


def save_assessment(
    *,
    assessment_id: str,
    patient_record: dict[str, Any],
    structured: dict[str, Any],
    created_at: str | None = None,
    db_path: Path | None = None,
) -> str:
    """Insert one assessment. Uses parameterized SQL."""
    init_db(db_path)
    timestamp = created_at or utc_now_iso()
    with _connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO assessments (
                id, created_at, age, gender, symptoms, duration, severity,
                response_language, urgency_level, summary, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assessment_id,
                timestamp,
                patient_record.get("age"),
                patient_record.get("gender"),
                patient_record.get("symptoms"),
                patient_record.get("duration"),
                patient_record.get("severity"),
                patient_record.get("response_language"),
                structured.get("urgency_level"),
                structured.get("summary"),
                json.dumps(structured, ensure_ascii=False),
            ),
        )
        connection.commit()
    return assessment_id


def list_assessments(db_path: Path | None = None) -> list[dict[str, Any]]:
    init_db(db_path)
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, age, gender, symptoms, duration, severity,
                   response_language, urgency_level, summary
            FROM assessments
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_assessment(assessment_id: str, db_path: Path | None = None) -> dict[str, Any] | None:
    init_db(db_path)
    with _connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM assessments WHERE id = ?",
            (assessment_id,),
        ).fetchone()
    if row is None:
        return None
    record = dict(row)
    try:
        record["structured"] = json.loads(record.get("result_json") or "{}")
    except json.JSONDecodeError:
        record["structured"] = None
    return record


def delete_assessment(assessment_id: str, db_path: Path | None = None) -> bool:
    init_db(db_path)
    with _connect(db_path) as connection:
        cursor = connection.execute(
            "DELETE FROM assessments WHERE id = ?",
            (assessment_id,),
        )
        connection.commit()
        deleted = cursor.rowcount > 0
    return deleted


def clear_all_history(db_path: Path | None = None) -> int:
    init_db(db_path)
    with _connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM assessments")
        connection.commit()
        count = cursor.rowcount if cursor.rowcount is not None else 0
    LOGGER.info("Assessment history cleared")
    return count
