"""
Input and response validation for MediGuide AI.

Students: validation happens before any AI call.
If the form is incomplete or the JSON is broken,
we stop early and show a friendly message.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.config import (
    AGE_MAX,
    AGE_MIN,
    ALLOWED_URGENCY_LEVELS,
    RESPONSE_LANGUAGES,
    SEVERITY_MAX,
    SEVERITY_MIN,
)

def looks_like_openai_api_key(value: str) -> bool:
    """
    Cheap format check for a user-typed OpenAI key.

    This does not prove the key is valid or billed. It only rejects
    empty, spaced, or obviously wrong values before a live check.
    """
    text = (value or "").strip()
    if not text.startswith("sk-"):
        return False
    if len(text) < 20:
        return False
    if any(ch.isspace() for ch in text):
        return False
    return True


REQUIRED_RESPONSE_FIELDS = (
    "summary",
    "possible_conditions",
    "urgency_level",
    "recommended_next_steps",
    "questions_for_doctor",
    "warning_signs",
)


@dataclass
class PatientInput:
    """Clean, validated patient form data used by the rest of the app."""

    age: int
    gender: str
    symptoms: list[str]
    free_text_symptoms: str
    duration: str
    severity: int
    medical_conditions: str
    medications: str
    additional_notes: str
    response_language: str
    extra_details: dict[str, str] = field(default_factory=dict)

    def combined_symptoms(self) -> list[str]:
        combined = [item.strip() for item in self.symptoms if item.strip()]
        extra = self.free_text_symptoms.strip()
        if extra:
            combined.append(extra)
        return combined

    def symptom_text(self) -> str:
        return ", ".join(self.combined_symptoms())

    def extra_context_text(self) -> str:
        """Turn optional intake answers into prompt text."""
        lines = []
        for label, value in (self.extra_details or {}).items():
            text = str(value).strip()
            if text:
                lines.append(f"{label}: {text}")
        return "\n".join(lines) if lines else "Not provided"

    def to_prompt_variables(self) -> dict[str, Any]:
        """Values that fill PromptTemplate / ChatPromptTemplate variables."""
        return {
            "age": str(self.age),
            "gender": self.gender,
            "symptoms": self.symptom_text() or "Not provided",
            "duration": self.duration,
            "severity": str(self.severity),
            "medical_conditions": self.medical_conditions.strip() or "Not provided",
            "medications": self.medications.strip() or "Not provided",
            "additional_notes": self.additional_notes.strip() or "Not provided",
            "extra_context": self.extra_context_text(),
            "response_language": self.response_language,
        }

    def to_history_record(self) -> dict[str, Any]:
        """
        Fields that may be stored in optional history.

        Medications, medical conditions, and additional notes are excluded
        so history does not quietly keep extra sensitive details.
        """
        return {
            "age": self.age,
            "gender": self.gender,
            "symptoms": self.symptom_text(),
            "duration": self.duration,
            "severity": self.severity,
            "response_language": self.response_language,
        }


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    patient: PatientInput | None = None
    data: dict[str, Any] | None = None
    notes: list[str] = field(default_factory=list)


def validate_age(raw_age: str | int | None) -> tuple[int | None, str | None]:
    """
    Age is collected with st.text_input, so it arrives as text.

    Reject empty, non-numeric, negative, and implausible values.
    """
    if raw_age is None:
        return None, "Please enter an age."

    text = str(raw_age).strip()
    if text == "":
        return None, "Please enter an age."

    if not re_full_int(text):
        return None, "Age must be a whole number, for example 25."

    age = int(text)
    if age < AGE_MIN or age > AGE_MAX:
        return None, f"Please enter an age between {AGE_MIN} and {AGE_MAX}."
    return age, None


def re_full_int(text: str) -> bool:
    """Return True only for an optional sign plus digits. No decimals."""
    if text.startswith("-"):
        digits = text[1:]
        return digits.isdigit()
    return text.isdigit()


def validate_severity(raw_severity: int | str | None) -> tuple[int | None, str | None]:
    if raw_severity is None or str(raw_severity).strip() == "":
        return None, "Please choose a severity from 1 to 10."
    try:
        value = int(raw_severity)
    except (TypeError, ValueError):
        return None, "Severity must be a whole number from 1 to 10."
    if value < SEVERITY_MIN or value > SEVERITY_MAX:
        return None, f"Severity must be between {SEVERITY_MIN} and {SEVERITY_MAX}."
    return value, None


def validate_symptoms(selected: list[str] | None, free_text: str | None) -> tuple[list[str], str, str | None]:
    """
    Users may pick common symptoms, type a description, or both.

    A predefined symptom is not required when free-text is valid.
    """
    chosen = [item.strip() for item in (selected or []) if str(item).strip()]
    extra = (free_text or "").strip()
    if not chosen and not extra:
        return [], "", "Please select at least one symptom or describe the symptoms in your own words."
    if extra and len(extra) < 3:
        return chosen, extra, "Please add a little more detail in the symptom description (at least 3 characters)."
    return chosen, extra, None


def validate_patient_input(
    *,
    age: str | int | None,
    gender: str | None,
    symptoms: list[str] | None,
    free_text_symptoms: str | None,
    duration: str | None,
    severity: int | str | None,
    medical_conditions: str | None = "",
    medications: str | None = "",
    additional_notes: str | None = "",
    response_language: str | None = "English",
    extra_details: dict[str, str] | None = None,
) -> ValidationResult:
    """Validate the full assessment form. Used by the UI and by tests."""
    errors: list[str] = []

    parsed_age, age_error = validate_age(age)
    if age_error:
        errors.append(age_error)

    parsed_severity, severity_error = validate_severity(severity)
    if severity_error:
        errors.append(severity_error)

    chosen, extra, symptom_error = validate_symptoms(symptoms, free_text_symptoms)
    if symptom_error:
        errors.append(symptom_error)

    gender_value = (gender or "").strip() or "Prefer not to say"
    duration_value = (duration or "").strip()
    if not duration_value:
        errors.append("Please choose how long the symptoms have lasted.")

    language = (response_language or "English").strip()
    if language not in RESPONSE_LANGUAGES:
        errors.append("Please choose English or Urdu as the response language.")

    if errors:
        return ValidationResult(ok=False, errors=errors)

    patient = PatientInput(
        age=parsed_age if parsed_age is not None else 0,
        gender=gender_value,
        symptoms=chosen,
        free_text_symptoms=extra,
        duration=duration_value,
        severity=parsed_severity if parsed_severity is not None else 1,
        medical_conditions=(medical_conditions or "").strip(),
        medications=(medications or "").strip(),
        additional_notes=(additional_notes or "").strip(),
        response_language=language,
        extra_details=_clean_extra_details(extra_details),
    )
    return ValidationResult(ok=True, patient=patient)


_SKIP_EXTRA_ANSWERS = {
    "prefer not to say",
    "unknown / prefer not to say",
    "unsure",
}


def _clean_extra_details(raw: dict[str, str] | None) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for label, value in (raw or {}).items():
        text = str(value or "").strip()
        if text and text.lower() not in _SKIP_EXTRA_ANSWERS:
            cleaned[str(label)] = text
    return cleaned


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items: list[str] = []
        for entry in value:
            if entry is None:
                continue
            text = str(entry).strip()
            if text:
                items.append(text)
        return items
    text = str(value).strip()
    return [text] if text else []


def _normalize_condition(entry: Any) -> dict[str, str] | None:
    if isinstance(entry, str):
        name = entry.strip()
        if not name:
            return None
        return {
            "name": name,
            "reason": "The model did not explain this possibility. Treat it as uncertain educational information only.",
        }
    if not isinstance(entry, dict):
        return None
    name = str(entry.get("name") or "").strip()
    reason = str(entry.get("reason") or "").strip()
    if not name:
        return None
    if not reason:
        reason = "This is a possibility to discuss with a healthcare professional, not a confirmed diagnosis."
    return {"name": name, "reason": reason}


def validate_assessment_response(payload: dict[str, Any] | None) -> ValidationResult:
    """
    Check that the model JSON has the required shape.

    Missing lists become empty lists. Invalid urgency is never treated as LOW.
    Conditions are never turned into confirmed diagnoses.
    """
    notes: list[str] = []
    if not isinstance(payload, dict):
        return ValidationResult(
            ok=False,
            errors=["The AI response did not contain a JSON object with the required fields."],
        )

    missing = [key for key in REQUIRED_RESPONSE_FIELDS if key not in payload]
    if missing:
        notes.append(
            "Some expected fields were missing from the AI response: "
            + ", ".join(missing)
            + ". Empty placeholders were used so the page does not crash."
        )

    summary = str(payload.get("summary") or "").strip()
    if not summary:
        summary = (
            "The model did not provide a summary. This is educational information only "
            "and is not a diagnosis."
        )
        notes.append("The summary field was missing or empty.")

    raw_conditions = payload.get("possible_conditions") or []
    conditions: list[dict[str, str]] = []
    if not isinstance(raw_conditions, list):
        notes.append("possible_conditions was not a list, so it was ignored.")
        raw_conditions = []
    for entry in raw_conditions:
        normalized = _normalize_condition(entry)
        if normalized:
            conditions.append(normalized)

    urgency = str(payload.get("urgency_level") or "").strip().upper()
    if urgency not in ALLOWED_URGENCY_LEVELS:
        # Conservative default: never fall back to LOW when the label is unusable.
        urgency = "MEDIUM"
        notes.append(
            "The model returned an invalid or missing urgency label. "
            "A conservative MEDIUM placeholder was used. This is not a clinical triage score."
        )

    data = {
        "summary": summary,
        "possible_conditions": conditions,
        "urgency_level": urgency,
        "recommended_next_steps": _as_string_list(payload.get("recommended_next_steps")),
        "questions_for_doctor": _as_string_list(payload.get("questions_for_doctor")),
        "warning_signs": _as_string_list(payload.get("warning_signs")),
    }
    return ValidationResult(ok=True, data=data, notes=notes)
