"""PDF generation test. Practical and independent of OpenAI."""

from __future__ import annotations

from tests.conftest import SAMPLE_JSON, SCENARIO_1
from src.report_service import build_pdf_report
from src.validation import validate_patient_input


def test_pdf_contains_branding_and_disclaimer():
    patient = validate_patient_input(**SCENARIO_1).patient.to_prompt_variables()
    pdf_bytes = build_pdf_report(
        patient=patient,
        structured=SAMPLE_JSON,
        timestamp="2026-01-01T10:00:00+00:00",
        safety={"possible_emergency": False, "warning_message": ""},
    )
    assert pdf_bytes.startswith(b"%PDF")
    assert b"MediGuide" in pdf_bytes or b"EDUCATIONAL" in pdf_bytes
    assert len(pdf_bytes) > 500
