"""Tests for deterministic emergency checks. These tests never call an API."""

from __future__ import annotations

from tests.conftest import SCENARIO_1, SCENARIO_3
from src.medical_safety import check_emergency_signs, collect_search_text


def test_mild_cold_symptoms_are_not_flagged_as_emergency():
    result = check_emergency_signs(
        symptoms=SCENARIO_1["symptoms"],
        free_text=SCENARIO_1["free_text_symptoms"],
    )
    assert result.possible_emergency is False
    assert result.warning_message == ""


def test_scenario_3_chest_pain_and_breathlessness():
    result = check_emergency_signs(
        symptoms=SCENARIO_3["symptoms"],
        free_text=SCENARIO_3["free_text_symptoms"],
    )
    assert result.possible_emergency is True
    assert result.warning_message
    assert "emergency" in result.warning_message.lower()


def test_emergency_warning_does_not_require_api(monkeypatch):
    """The safety scan must not import or call the model layer."""
    import src.medical_safety as medical_safety

    def fail_if_model_touched(*_args, **_kwargs):
        raise AssertionError("Safety checks must not call the model")

    monkeypatch.setattr("src.chains.run_structured_assessment", fail_if_model_touched, raising=False)
    result = medical_safety.check_emergency_signs(
        symptoms=["Chest pain"],
        free_text="severe difficulty breathing",
    )
    assert result.possible_emergency is True


def test_stroke_like_phrases():
    result = check_emergency_signs(free_text="sudden facial drooping and slurred speech")
    assert result.possible_emergency is True
    assert any("droop" in item or "speech" in item for item in result.matched_signs)


def test_unconsciousness():
    result = check_emergency_signs(free_text="passed out and cannot wake")
    assert result.possible_emergency is True


def test_severe_bleeding():
    result = check_emergency_signs(free_text="severe uncontrolled bleeding")
    assert result.possible_emergency is True


def test_allergic_reaction_with_breathing():
    result = check_emergency_signs(free_text="severe allergic reaction with throat swelling")
    assert result.possible_emergency is True


def test_missing_keyword_note_is_present():
    result = check_emergency_signs(symptoms=["Headache"])
    assert "incomplete" in result.incomplete_list_note.lower() or "missing" in result.incomplete_list_note.lower()


def test_search_text_combines_fields():
    text = collect_search_text(["Fever"], "also dizzy", "note")
    assert "fever" in text
    assert "dizzy" in text
