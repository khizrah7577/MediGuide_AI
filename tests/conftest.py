"""Shared sample data for MediGuide AI tests. No real patient information."""

from __future__ import annotations

SAMPLE_JSON = {
    "summary": "Educational information only. This is not a diagnosis.",
    "possible_conditions": [
        {
            "name": "Common viral cold-type illness (possible, unconfirmed)",
            "reason": "Runny nose and sore throat can have many causes. This is a possibility to discuss, not a confirmed diagnosis.",
        }
    ],
    "urgency_level": "LOW",
    "recommended_next_steps": [
        "Monitor symptoms",
        "Speak with a qualified healthcare professional if symptoms worsen",
    ],
    "questions_for_doctor": ["Should I be examined in person?"],
    "warning_signs": ["Seek emergency care for severe breathing difficulty or chest pain"],
}

SCENARIO_1 = {
    "age": "25",
    "gender": "Prefer not to say",
    "symptoms": ["Runny nose", "Sore throat"],
    "free_text_symptoms": "",
    "duration": "1–3 days",
    "severity": 2,
    "medical_conditions": "",
    "medications": "",
    "additional_notes": "",
    "response_language": "English",
}

SCENARIO_2 = {
    "age": "40",
    "gender": "Prefer not to say",
    "symptoms": ["Fever", "Cough"],
    "free_text_symptoms": "",
    "duration": "4–7 days",
    "severity": 6,
    "medical_conditions": "",
    "medications": "",
    "additional_notes": "",
    "response_language": "English",
}

SCENARIO_3 = {
    "age": "50",
    "gender": "Prefer not to say",
    "symptoms": ["Chest pain", "Shortness of breath"],
    "free_text_symptoms": "severe chest pain",
    "duration": "Less than 24 hours",
    "severity": 9,
    "medical_conditions": "",
    "medications": "",
    "additional_notes": "",
    "response_language": "English",
}

SCENARIO_5_NO_SYMPTOMS = {
    "age": "30",
    "gender": "Prefer not to say",
    "symptoms": [],
    "free_text_symptoms": "",
    "duration": "1–3 days",
    "severity": 3,
    "medical_conditions": "",
    "medications": "",
    "additional_notes": "",
    "response_language": "English",
}

SCENARIO_6_URDU = {
    "age": "28",
    "gender": "Prefer not to say",
    "symptoms": ["Headache"],
    "free_text_symptoms": "",
    "duration": "1–3 days",
    "severity": 3,
    "medical_conditions": "",
    "medications": "",
    "additional_notes": "",
    "response_language": "Urdu",
}
