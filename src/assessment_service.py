"""
Assessment orchestrator for MediGuide AI.

This is the conductor of the application:
1. Validate input
2. Run deterministic emergency checks (no API)
3. Stop if the API key is missing
4. Call LLMChain for structured JSON
5. Parse and validate JSON
6. Overlay safety on the model urgency label
7. Optionally save history

Streaming of the educational explanation is started later by the UI
with st.write_stream(), because Streamlit needs to render it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from src.chains import (
    MissingAPIKeyError,
    classify_llm_error,
    run_structured_assessment,
    stream_educational_explanation,
)
from src.config import has_api_key
from src.history_service import save_assessment
from src.medical_safety import SafetyCheckResult, check_emergency_signs
from src.utils import LOGGER, new_assessment_id, parse_json_safely, utc_now_iso
from src.validation import PatientInput, validate_assessment_response, validate_patient_input


@dataclass
class AssessmentOutcome:
    """Everything the UI needs to render results or an error."""

    success: bool
    assessment_id: str
    timestamp: str
    patient: PatientInput | None = None
    structured: dict[str, Any] | None = None
    safety: SafetyCheckResult | None = None
    parse_notes: list[str] = field(default_factory=list)
    error: str | None = None
    skipped_model: bool = False
    model_called: bool = False
    raw_model_text: str | None = None

    def to_session_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "assessment_id": self.assessment_id,
            "timestamp": self.timestamp,
            "patient": self.patient.to_prompt_variables() if self.patient else None,
            "patient_history": self.patient.to_history_record() if self.patient else None,
            "structured": self.structured,
            "safety": {
                "possible_emergency": bool(self.safety and self.safety.possible_emergency),
                "matched_signs": self.safety.matched_signs if self.safety else [],
                "warning_message": self.safety.warning_message if self.safety else "",
                "urdu_warning_message": self.safety.urdu_warning_message if self.safety else "",
                "incomplete_list_note": self.safety.incomplete_list_note if self.safety else "",
            },
            "parse_notes": self.parse_notes,
            "error": self.error,
            "skipped_model": self.skipped_model,
            "model_called": self.model_called,
        }


def run_safety_only(
    *,
    symptoms: list[str] | None,
    free_text_symptoms: str = "",
    additional_notes: str = "",
) -> SafetyCheckResult:
    """Emergency check that never contacts the model. Used by tests and the UI."""
    return check_emergency_signs(
        symptoms=symptoms,
        free_text=free_text_symptoms,
        additional_notes=additional_notes,
    )


def run_assessment(
    form_data: dict[str, Any],
    *,
    llm: Any | None = None,
    save_history: bool = False,
    allow_model: bool = True,
) -> AssessmentOutcome:
    """
    Run a full assessment from validated form data.

    llm can be a fake chat model in tests so no paid API call is made.
    """
    assessment_id = new_assessment_id()
    timestamp = utc_now_iso()

    validation = validate_patient_input(**form_data)
    if not validation.ok or validation.patient is None:
        return AssessmentOutcome(
            success=False,
            assessment_id=assessment_id,
            timestamp=timestamp,
            error=" ".join(validation.errors) or "The form is incomplete.",
            skipped_model=True,
        )

    patient = validation.patient
    safety = run_safety_only(
        symptoms=patient.symptoms,
        free_text_symptoms=patient.free_text_symptoms,
        additional_notes=" ".join(
            part for part in (patient.additional_notes, patient.extra_context_text()) if part
        ),
    )

    if not allow_model or (llm is None and not has_api_key()):
        return AssessmentOutcome(
            success=False if not safety.possible_emergency else True,
            assessment_id=assessment_id,
            timestamp=timestamp,
            patient=patient,
            safety=safety,
            skipped_model=True,
            error=(
                None
                if safety.possible_emergency and not allow_model
                else (
                    "Live AI assessment is unavailable because no OpenAI API key is configured. "
                    "You can still use the form and the emergency safety check. "
                    "Sign in on the clinic login page with your OpenAI API key."
                )
            ),
            structured=_emergency_placeholder_structured(patient, safety) if safety.possible_emergency else None,
        )

    try:
        raw_text = run_structured_assessment(patient.to_prompt_variables(), llm=llm)
    except MissingAPIKeyError as exc:
        return AssessmentOutcome(
            success=False,
            assessment_id=assessment_id,
            timestamp=timestamp,
            patient=patient,
            safety=safety,
            skipped_model=True,
            error=str(exc),
        )
    except Exception as exc:
        LOGGER.warning("Assessment model call failed type=%s id=%s", type(exc).__name__, assessment_id)
        return AssessmentOutcome(
            success=False,
            assessment_id=assessment_id,
            timestamp=timestamp,
            patient=patient,
            safety=safety,
            model_called=True,
            error=classify_llm_error(exc),
        )

    parsed, parse_error = parse_json_safely(raw_text)
    if parse_error or parsed is None:
        return AssessmentOutcome(
            success=False,
            assessment_id=assessment_id,
            timestamp=timestamp,
            patient=patient,
            safety=safety,
            model_called=True,
            raw_model_text=None,  # do not keep raw payload in logs or session dumps
            error=parse_error or "The AI response could not be parsed.",
        )

    response_validation = validate_assessment_response(parsed)
    if not response_validation.ok or response_validation.data is None:
        return AssessmentOutcome(
            success=False,
            assessment_id=assessment_id,
            timestamp=timestamp,
            patient=patient,
            safety=safety,
            model_called=True,
            error=" ".join(response_validation.errors),
        )

    structured = dict(response_validation.data)
    structured["urgency_level"] = safety.overlay_urgency(structured["urgency_level"])
    if safety.possible_emergency:
        warning = safety.warning_message
        if warning and warning not in structured["warning_signs"]:
            structured["warning_signs"] = [warning, *structured["warning_signs"]]

    if save_history:
        try:
            save_assessment(
                assessment_id=assessment_id,
                patient_record=patient.to_history_record(),
                structured=structured,
                created_at=timestamp,
            )
        except Exception:
            LOGGER.warning("History save failed id=%s", assessment_id)

    return AssessmentOutcome(
        success=True,
        assessment_id=assessment_id,
        timestamp=timestamp,
        patient=patient,
        structured=structured,
        safety=safety,
        parse_notes=response_validation.notes,
        model_called=True,
    )


def _emergency_placeholder_structured(
    patient: PatientInput,
    safety: SafetyCheckResult,
) -> dict[str, Any]:
    """
    Local educational placeholder used when an emergency is flagged
    and the model is not called. This is application text, not AI output.
    """
    return {
        "summary": (
            "A possible emergency warning was raised from the symptom description "
            f"({patient.symptom_text()}). No AI model was used for this warning. "
            "Seek emergency medical help immediately. This is not a diagnosis."
        ),
        "possible_conditions": [
            {
                "name": "Possible medical emergency — not classified by this app",
                "reason": (
                    "The app's keyword safety check found warning signs "
                    f"({', '.join(safety.matched_signs) or 'unspecified'}). "
                    "This is not a diagnosis and is not a complete emergency screen."
                ),
            }
        ],
        "urgency_level": "EMERGENCY",
        "recommended_next_steps": [
            "Seek emergency medical help immediately.",
            "Contact local emergency services or go to the nearest emergency department.",
            "Do not wait for an AI response or for this application to finish.",
        ],
        "questions_for_doctor": [
            "What warning signs should I treat as an emergency?",
            "What information should I bring to an emergency department?",
        ],
        "warning_signs": [safety.warning_message] if safety.warning_message else [],
    }


def build_explanation_stream(patient_variables: dict[str, Any], structured: dict[str, Any], llm: Any | None = None):
    """Return a generator the UI can pass to st.write_stream()."""
    payload = json.dumps(structured, ensure_ascii=False)
    return stream_educational_explanation(patient_variables, payload, llm=llm)
