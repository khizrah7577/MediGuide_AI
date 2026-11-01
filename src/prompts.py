"""
LangChain prompts for MediGuide AI.

This file demonstrates:
- PromptTemplate
- ChatPromptTemplate
- SystemMessage / HumanMessage / AIMessage (educational demo)

Students: a prompt is the instruction we send to the model.
The system message sets the rules. The human message contains
the patient's described symptoms.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from src.config import MEDICAL_DISCLAIMER

# The model must return exactly this JSON shape.
JSON_SCHEMA_INSTRUCTIONS = """
Return ONLY a JSON object with exactly these top-level fields:
{
  "summary": "",
  "possible_conditions": [
    {
      "name": "",
      "reason": ""
    }
  ],
  "urgency_level": "LOW",
  "recommended_next_steps": [],
  "questions_for_doctor": [],
  "warning_signs": []
}

urgency_level must be one of: LOW, MEDIUM, HIGH, EMERGENCY.
Do not wrap the JSON in Markdown fences.
Do not add extra top-level keys.
"""

SYSTEM_TEMPLATE = """You are MediGuide AI, an educational health-information assistant.
You help people organize symptoms and prepare questions for a qualified healthcare professional.

Hard safety rules:
- You do not provide a medical diagnosis.
- You never claim to confirm a disease.
- You never present possible conditions as established diagnoses.
- You never guarantee that symptoms are harmless.
- You never guarantee that the person is safe because an urgency label is LOW.
- You never recommend ignoring severe, sudden, or worsening symptoms.
- You never replace a doctor's examination, tests, or emergency services.
- You avoid unsupported medication dosages and personalized prescribing.
- You do not tell anyone to start, stop, or change prescribed treatment.
- You explain uncertainty in simple language.
- You encourage professional medical evaluation where appropriate.
- If emergency warning signs are described, you set urgency_level to EMERGENCY
  and tell the person to seek emergency care immediately.
- If you are unsure, say you are unsure. Do not invent clinical certainty.

{disclaimer}

Write all JSON text values in {response_language}.
Keep emergency guidance clear even when the language is Urdu.
Each possible condition must include a short reason and uncertainty wording
such as "this is one possibility to discuss, not a confirmed diagnosis".

{json_schema}
"""

HUMAN_TEMPLATE = """Please generate educational information for the following user-described details.

Age: {age}
Gender (user-selected, do not infer): {gender}
Symptoms: {symptoms}
Duration: {duration}
Perceived severity (user's own 1-10 rating, not a clinical score): {severity}
Existing medical conditions (may be empty): {medical_conditions}
Current medications (may be empty; do not prescribe or advise stopping): {medications}
Additional notes (may be empty): {additional_notes}
Additional intake details (may be empty): {extra_context}
Requested response language: {response_language}

Remember: return JSON only. This is educational information, not a diagnosis.
"""

# PromptTemplate is required by the assignment. It fills in patient fields.
PATIENT_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=[
        "age",
        "gender",
        "symptoms",
        "duration",
        "severity",
        "medical_conditions",
        "medications",
        "additional_notes",
        "extra_context",
        "response_language",
    ],
    template=HUMAN_TEMPLATE,
)

# ChatPromptTemplate is the real chat-style prompt used with ChatOpenAI.
ASSESSMENT_CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_TEMPLATE),
        ("human", HUMAN_TEMPLATE),
    ]
)

EXPLANATION_SYSTEM = """You are MediGuide AI. Write a short educational explanation
for a layperson. Do not claim to diagnose. Do not prescribe medication.
Do not say the person is safe. Encourage professional medical advice.
If emergency warning signs may be present, say they should seek emergency help now.
Write in {response_language}. Use plain paragraphs, not JSON.
"""

EXPLANATION_HUMAN = """Patient-described symptoms: {symptoms}
Duration: {duration}
Perceived severity: {severity}/10
Requested language: {response_language}

Structured educational JSON already produced for this same assessment:
{structured_json}

Write 2-4 short paragraphs the user can read while waiting to speak with a clinician.
"""

EXPLANATION_CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", EXPLANATION_SYSTEM),
        ("human", EXPLANATION_HUMAN),
    ]
)


def get_assessment_prompt_variables(patient_variables: dict) -> dict:
    """Add disclaimer and JSON schema to the patient variables."""
    filled = dict(patient_variables)
    filled.setdefault("response_language", "English")
    filled.setdefault("extra_context", "Not provided")
    filled["disclaimer"] = MEDICAL_DISCLAIMER
    filled["json_schema"] = JSON_SCHEMA_INSTRUCTIONS
    return filled


def get_message_demonstration() -> list:
    """
    Educational demonstration of LangChain message types.

    This is NOT a live model response. The AIMessage is a fixed example
    written for teaching SystemMessage, HumanMessage, and AIMessage.
    """
    return [
        SystemMessage(
            content=(
                "You are MediGuide AI, an educational assistant. "
                "You do not diagnose disease. You explain general information "
                "and encourage people to speak with a qualified clinician."
            )
        ),
        HumanMessage(
            content=(
                "I have had a mild runny nose for one day. "
                "Please explain the LangChain message types using this example."
            )
        ),
        AIMessage(
            content=(
                "This is an EDUCATIONAL demonstration, not a live AI medical result. "
                "SystemMessage sets the assistant's rules. HumanMessage carries the "
                "user's words. AIMessage is the assistant reply object used by LangChain. "
                "In the real assessment workflow, the live model response is generated "
                "separately and is never replaced by this demonstration text."
            )
        ),
    ]


CHAT_FOLLOWUP_SYSTEM = """You are MediGuide AI, a professional educational health assistant
in a clinic-style chat. Speak calmly, clearly, and with empathy.

Hard safety rules:
- You do not provide a medical diagnosis.
- You never claim to confirm a disease.
- You never guarantee that symptoms are harmless or that the person is safe.
- You never prescribe medication or tell anyone to stop prescribed treatment.
- You never replace a doctor, emergency service, or medical examination.
- If emergency warning signs are described, tell the person to seek emergency
  care immediately and do not delay that guidance.
- Explain uncertainty in simple language.
- Keep answers short enough for a chat bubble (about 2-5 short paragraphs).

{disclaimer}

Write in {response_language}. Keep emergency warnings easy to notice.
"""

CHAT_FOLLOWUP_HUMAN = """Earlier educational summary (not a diagnosis):
{prior_summary}

Recent chat:
{conversation}

Latest user message:
{user_message}

Reply as MediGuide AI. Do not invent test results. Do not claim certainty.
"""

CHAT_FOLLOWUP_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", CHAT_FOLLOWUP_SYSTEM),
        ("human", CHAT_FOLLOWUP_HUMAN),
    ]
)


def format_patient_human_message(patient_variables: dict) -> str:
    """Use PromptTemplate to build the human-message body."""
    return PATIENT_PROMPT_TEMPLATE.format(**patient_variables)
