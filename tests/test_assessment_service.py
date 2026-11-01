"""Tests for assessment orchestration using mocked model output."""

from __future__ import annotations

import json

from tests.conftest import (
    SAMPLE_JSON,
    SCENARIO_1,
    SCENARIO_2,
    SCENARIO_3,
    SCENARIO_5_NO_SYMPTOMS,
    SCENARIO_6_URDU,
)
from src.assessment_service import run_assessment, run_safety_only
from src.prompts import PATIENT_PROMPT_TEMPLATE, get_assessment_prompt_variables, get_message_demonstration


class FakeChatModel:
    """Tiny stand-in so tests never call OpenAI."""

    def __init__(self, text: str):
        self.text = text
        self.invoke_count = 0

    def invoke(self, _messages):
        self.invoke_count += 1
        return type("Resp", (), {"content": self.text})()

    def stream(self, _messages):
        self.invoke_count += 1
        yield type("Chunk", (), {"content": self.text})()


def test_scenario_1_with_mocked_model(monkeypatch):
    fake = FakeChatModel(json.dumps(SAMPLE_JSON))
    monkeypatch.setattr(
        "src.assessment_service.run_structured_assessment",
        lambda _vars, llm=None: fake.invoke([]).content,
    )
    monkeypatch.setattr("src.assessment_service.has_api_key", lambda: True)
    outcome = run_assessment(SCENARIO_1, llm=fake)
    assert outcome.success
    assert outcome.model_called
    assert outcome.structured["urgency_level"] in {"LOW", "MEDIUM", "HIGH", "EMERGENCY"}
    assert outcome.patient.age == 25


def test_scenario_2_with_mocked_model(monkeypatch):
    payload = dict(SAMPLE_JSON)
    payload["urgency_level"] = "MEDIUM"
    monkeypatch.setattr(
        "src.assessment_service.run_structured_assessment",
        lambda _vars, llm=None: json.dumps(payload),
    )
    monkeypatch.setattr("src.assessment_service.has_api_key", lambda: True)
    outcome = run_assessment(SCENARIO_2, llm=FakeChatModel("unused"))
    assert outcome.success
    assert outcome.structured["urgency_level"] == "MEDIUM"


def test_scenario_3_emergency_without_model_call(monkeypatch):
    def fail_model(*_args, **_kwargs):
        raise AssertionError("Emergency warning must not require a model call")

    monkeypatch.setattr("src.assessment_service.run_structured_assessment", fail_model)
    safety = run_safety_only(
        symptoms=SCENARIO_3["symptoms"],
        free_text_symptoms=SCENARIO_3["free_text_symptoms"],
    )
    assert safety.possible_emergency is True

    outcome = run_assessment(SCENARIO_3, allow_model=False)
    assert outcome.skipped_model is True
    assert outcome.safety.possible_emergency is True
    assert outcome.structured["urgency_level"] == "EMERGENCY"


def test_emergency_overrides_low_model_urgency(monkeypatch):
    payload = dict(SAMPLE_JSON)
    payload["urgency_level"] = "LOW"
    monkeypatch.setattr(
        "src.assessment_service.run_structured_assessment",
        lambda _vars, llm=None: json.dumps(payload),
    )
    monkeypatch.setattr("src.assessment_service.has_api_key", lambda: True)
    outcome = run_assessment(SCENARIO_3, llm=FakeChatModel("unused"))
    assert outcome.structured["urgency_level"] == "EMERGENCY"


def test_scenario_5_missing_symptoms_does_not_call_model(monkeypatch):
    def fail_model(*_args, **_kwargs):
        raise AssertionError("Missing symptoms must not call the API")

    monkeypatch.setattr("src.assessment_service.run_structured_assessment", fail_model)
    outcome = run_assessment(SCENARIO_5_NO_SYMPTOMS)
    assert outcome.success is False
    assert outcome.skipped_model is True
    assert "symptom" in (outcome.error or "").lower()


def test_scenario_6_urdu_is_passed_to_prompt(monkeypatch):
    captured = {}

    def fake_run(variables, llm=None):
        captured.update(variables)
        return json.dumps(SAMPLE_JSON)

    monkeypatch.setattr("src.assessment_service.run_structured_assessment", fake_run)
    monkeypatch.setattr("src.assessment_service.has_api_key", lambda: True)
    outcome = run_assessment(SCENARIO_6_URDU, llm=FakeChatModel("unused"))
    assert outcome.success
    assert captured["response_language"] == "Urdu"


def test_missing_api_key_is_friendly(monkeypatch):
    monkeypatch.setattr("src.assessment_service.has_api_key", lambda: False)
    outcome = run_assessment(SCENARIO_1)
    assert outcome.skipped_model is True
    assert outcome.model_called is False
    assert "API key" in (outcome.error or "")


def test_malformed_model_json(monkeypatch):
    monkeypatch.setattr(
        "src.assessment_service.run_structured_assessment",
        lambda _vars, llm=None: "this is not json",
    )
    monkeypatch.setattr("src.assessment_service.has_api_key", lambda: True)
    outcome = run_assessment(SCENARIO_1, llm=FakeChatModel("unused"))
    assert outcome.success is False
    assert "JSON" in (outcome.error or "")


def test_prompt_template_contains_required_variables():
    variables = get_assessment_prompt_variables(
        {
            "age": "25",
            "gender": "Prefer not to say",
            "symptoms": "Runny nose",
            "duration": "1–3 days",
            "severity": "2",
            "medical_conditions": "Not provided",
            "medications": "Not provided",
            "additional_notes": "Not provided",
            "response_language": "English",
        }
    )
    text = PATIENT_PROMPT_TEMPLATE.format(**{
        k: variables[k]
        for k in PATIENT_PROMPT_TEMPLATE.input_variables
    })
    assert "25" in text
    assert "Runny nose" in text


def test_message_demonstration_is_labelled_educational():
    messages = get_message_demonstration()
    names = [type(item).__name__ for item in messages]
    assert names == ["SystemMessage", "HumanMessage", "AIMessage"]
    assert "EDUCATIONAL" in messages[-1].content
