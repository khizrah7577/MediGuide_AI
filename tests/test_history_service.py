"""Tests for optional SQLite history."""

from __future__ import annotations

from tests.conftest import SAMPLE_JSON
from src.history_service import (
    clear_all_history,
    delete_assessment,
    get_assessment,
    list_assessments,
    save_assessment,
)


def test_history_create_retrieve_delete(tmp_path):
    db_path = tmp_path / "history.sqlite"
    patient = {
        "age": 25,
        "gender": "Prefer not to say",
        "symptoms": "Runny nose, Sore throat",
        "duration": "1–3 days",
        "severity": 2,
        "response_language": "English",
    }
    save_assessment(
        assessment_id="abc123",
        patient_record=patient,
        structured=SAMPLE_JSON,
        created_at="2026-01-01T10:00:00+00:00",
        db_path=db_path,
    )
    rows = list_assessments(db_path=db_path)
    assert len(rows) == 1
    assert rows[0]["id"] == "abc123"
    assert rows[0]["urgency_level"] == "LOW"

    loaded = get_assessment("abc123", db_path=db_path)
    assert loaded is not None
    assert loaded["structured"]["summary"] == SAMPLE_JSON["summary"]
    assert "medications" not in loaded

    assert delete_assessment("abc123", db_path=db_path) is True
    assert list_assessments(db_path=db_path) == []


def test_clear_all_history(tmp_path):
    db_path = tmp_path / "history.sqlite"
    save_assessment(
        assessment_id="one",
        patient_record={"age": 20, "symptoms": "Cough", "duration": "1–3 days", "severity": 3},
        structured=SAMPLE_JSON,
        db_path=db_path,
    )
    save_assessment(
        assessment_id="two",
        patient_record={"age": 21, "symptoms": "Fever", "duration": "4–7 days", "severity": 4},
        structured=SAMPLE_JSON,
        db_path=db_path,
    )
    deleted = clear_all_history(db_path=db_path)
    assert deleted >= 2
    assert list_assessments(db_path=db_path) == []


def test_history_does_not_require_medications_field(tmp_path):
    db_path = tmp_path / "history.sqlite"
    save_assessment(
        assessment_id="no-meds",
        patient_record={"age": 33, "symptoms": "Headache", "duration": "Unsure", "severity": 2},
        structured=SAMPLE_JSON,
        db_path=db_path,
    )
    loaded = get_assessment("no-meds", db_path=db_path)
    assert loaded["symptoms"] == "Headache"
