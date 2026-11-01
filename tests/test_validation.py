"""Tests for patient input and JSON response validation."""

from __future__ import annotations

from tests.conftest import SCENARIO_1, SCENARIO_2, SCENARIO_5_NO_SYMPTOMS, SCENARIO_6_URDU
from src.validation import (
    looks_like_openai_api_key,
    validate_age,
    validate_assessment_response,
    validate_patient_input,
    validate_severity,
)


def test_valid_age():
    age, error = validate_age("25")
    assert age == 25
    assert error is None


def test_invalid_age_empty():
    age, error = validate_age("")
    assert age is None
    assert error


def test_invalid_age_negative():
    age, error = validate_age("-4")
    assert age is None
    assert "between" in error.lower() or "number" in error.lower()


def test_invalid_age_not_a_number():
    age, error = validate_age("twenty")
    assert age is None
    assert error


def test_invalid_age_implausible():
    age, error = validate_age("400")
    assert age is None
    assert error


def test_invalid_severity():
    value, error = validate_severity(0)
    assert value is None
    assert error


def test_valid_severity():
    value, error = validate_severity(6)
    assert value == 6
    assert error is None


def test_scenario_1_valid_input():
    result = validate_patient_input(**SCENARIO_1)
    assert result.ok
    assert result.patient is not None
    assert result.patient.age == 25
    assert "Runny nose" in result.patient.symptoms


def test_scenario_2_valid_input():
    result = validate_patient_input(**SCENARIO_2)
    assert result.ok
    assert result.patient.severity == 6


def test_scenario_5_missing_symptoms():
    result = validate_patient_input(**SCENARIO_5_NO_SYMPTOMS)
    assert not result.ok
    assert any("symptom" in item.lower() for item in result.errors)


def test_free_text_symptoms_are_enough():
    result = validate_patient_input(
        age="22",
        gender="Prefer not to say",
        symptoms=[],
        free_text_symptoms="mild scratchy throat",
        duration="1–3 days",
        severity=2,
        response_language="English",
    )
    assert result.ok


def test_scenario_6_urdu_language_accepted():
    result = validate_patient_input(**SCENARIO_6_URDU)
    assert result.ok
    assert result.patient.response_language == "Urdu"


def test_valid_json_response():
    payload = {
        "summary": "Educational only",
        "possible_conditions": [{"name": "Possible viral illness", "reason": "Uncertain example"}],
        "urgency_level": "LOW",
        "recommended_next_steps": ["Speak with a clinician"],
        "questions_for_doctor": ["Do I need an exam?"],
        "warning_signs": ["Chest pain would need emergency care"],
    }
    result = validate_assessment_response(payload)
    assert result.ok
    assert result.data["urgency_level"] == "LOW"


def test_missing_json_fields_are_handled_safely():
    result = validate_assessment_response({"summary": "Only summary"})
    assert result.ok
    assert result.data["possible_conditions"] == []
    assert result.data["urgency_level"] == "MEDIUM"
    assert result.notes


def test_invalid_urgency_is_not_treated_as_low():
    result = validate_assessment_response(
        {
            "summary": "Educational only",
            "possible_conditions": [],
            "urgency_level": "SAFE",
            "recommended_next_steps": [],
            "questions_for_doctor": [],
            "warning_signs": [],
        }
    )
    assert result.ok
    assert result.data["urgency_level"] == "MEDIUM"


def test_openai_key_format_accepts_typical_prefix():
    assert looks_like_openai_api_key("sk-abcdefghijklmnopqrstuvwxyz")


def test_extra_intake_details_are_optional_and_reach_the_prompt():
    result = validate_patient_input(
        **SCENARIO_1,
        extra_details={"City or area": "Lahore", "Sleep last night": "Fair"},
    )
    assert result.ok
    assert result.patient is not None
    assert "Lahore" in result.patient.extra_context_text()
    assert "Fair" in result.patient.to_prompt_variables()["extra_context"]
    skipped = validate_patient_input(
        **SCENARIO_1,
        extra_details={"Sleep last night": "Prefer not to say", "Symptom onset": "Unsure"},
    )
    assert skipped.ok
    assert skipped.patient is not None
    assert skipped.patient.extra_context_text() == "Not provided"


def test_openai_key_format_rejects_empty_and_spaces():
    assert not looks_like_openai_api_key("")
    assert not looks_like_openai_api_key("sk- short")
    assert not looks_like_openai_api_key("not-a-key")
    assert not looks_like_openai_api_key("sk-tiny")
