"""
Deterministic medical safety checks for MediGuide AI.

These checks run BEFORE any model call. They are keyword/pattern
rules, not a validated medical triage protocol.

Students: this is one of the most important files to explain.
A missing keyword does NOT mean an emergency is absent.
A LOW urgency label from the model can NEVER hide this warning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.config import get_local_emergency_number

# This list is incomplete on purpose. It is an educational safety net,
# not a complete emergency screening tool.
EMERGENCY_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bchest pain\b", "chest pain"),
    (r"\bpain in (the )?chest\b", "chest pain"),
    (r"\bpressure in (the )?chest\b", "chest pressure"),
    (r"\btightness in (the )?chest\b", "chest tightness"),
    (r"\bshort(ness)? of breath\b", "shortness of breath"),
    (r"\bcan't breathe\b|\bcannot breathe\b|\bcan not breathe\b", "difficulty breathing"),
    (r"\bdifficulty breathing\b|\btrouble breathing\b|\bhard to breathe\b", "difficulty breathing"),
    (r"\bwheez(e|ing)\b.{0,40}\bbreath", "breathing difficulty"),
    (r"\bfacial droop|\bface droop|\bdrooping (face|smile)|uneven smile", "possible facial drooping"),
    (r"\bone[- ]sided weakness|\bweakness on one side|\bcan't (move|lift).{0,20}(arm|leg)", "one-sided weakness"),
    (r"\bsudden.{0,20}(weakness|numbness).{0,20}(arm|leg|face|side)", "sudden weakness"),
    (r"\bdifficulty speaking\b|\bcan't speak\b|\bcannot speak\b|\bslurred speech\b", "difficulty speaking"),
    (r"\bsudden.{0,20}speech|\bconfused speech|\bunable to speak", "sudden speech difficulty"),
    (r"\bunconscious\b|\bunresponsive\b|\bpassed out\b|\bcan't wake\b|\bcannot wake\b", "unconsciousness or inability to wake"),
    (r"\bsevere (uncontrolled )?bleeding\b|\bbleeding that (will not|won't) stop\b|\bhemorrhage\b", "severe bleeding"),
    (r"\bthroat swell|\bswelling.{0,20}throat|\btongue swell|\banaphyla", "possible severe allergic reaction"),
    (r"\bsevere allerg.{0,40}(breath|throat|swell)", "possible severe allergic reaction"),
    (r"\bblue lips\b|\bnot breathing\b|\bno pulse\b|\bcollapsed\b", "possible life-threatening emergency"),
    (r"\bsuicidal\b|\bkill myself\b|\bwant to die\b|\bend my life\b", "possible crisis requiring immediate help"),
)


EMERGENCY_HEADING = "Possible emergency warning"
EMERGENCY_BODY = (
    "The information you entered includes possible emergency warning signs. "
    "This app cannot rule out a medical emergency. Seek emergency medical help "
    "immediately. Contact local emergency services or go to the nearest "
    "emergency department. Do not wait for an AI response and do not rely on "
    "this application for emergency care."
)
URDU_EMERGENCY_BODY = (
    "درج کردہ معلومات میں ممکنہ ہنگامی علامات شامل ہو سکتی ہیں۔ "
    "اس ایپ سے ایمرجنسی کی تصدیق یا تردید نہیں کی جا سکتی۔ "
    "فوری طور پر مقامی ایمرجنسی خدمات سے رابطہ کریں یا قریبی ایمرجنسی ڈیپارٹمنٹ جائیں۔"
)
LOW_URGENCY_CAUTION = (
    "A LOW urgency label is only a visual category generated for education. "
    "It does not mean the symptoms are harmless, and it does not mean anyone "
    "is safe. Seek in-person care if symptoms are severe, sudden, worsening, "
    "or worrying."
)


@dataclass
class SafetyCheckResult:
    """Outcome of the deterministic safety scan."""

    possible_emergency: bool
    matched_signs: list[str] = field(default_factory=list)
    warning_message: str = ""
    urdu_warning_message: str = ""
    emergency_number: str = ""
    incomplete_list_note: str = (
        "This safety check looks for a limited set of warning phrases. "
        "If a phrase is missing, an emergency may still be present."
    )

    def overlay_urgency(self, model_urgency: str) -> str:
        """A model LOW/MEDIUM/HIGH label cannot hide an emergency warning."""
        if self.possible_emergency:
            return "EMERGENCY"
        return (model_urgency or "MEDIUM").upper()


def _normalize_for_search(text: str) -> str:
    lowered = (text or "").lower()
    lowered = lowered.replace("–", "-").replace("—", "-")
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered


def collect_search_text(
    symptoms: list[str] | None = None,
    free_text: str = "",
    additional_notes: str = "",
) -> str:
    """Combine user-entered symptom fields into one searchable string."""
    parts = [str(item) for item in (symptoms or [])]
    parts.append(free_text or "")
    parts.append(additional_notes or "")
    return _normalize_for_search(" ".join(parts))


def check_emergency_signs(
    symptoms: list[str] | None = None,
    free_text: str = "",
    additional_notes: str = "",
) -> SafetyCheckResult:
    """
    Scan the user's words for possible emergency warning signs.

    This function does not call any API.
    """
    haystack = collect_search_text(symptoms, free_text, additional_notes)
    matched: list[str] = []
    for pattern, label in EMERGENCY_PATTERNS:
        if re.search(pattern, haystack, flags=re.IGNORECASE):
            if label not in matched:
                matched.append(label)

    possible = bool(matched)
    number = get_local_emergency_number()
    warning = EMERGENCY_BODY
    if possible and number:
        warning += f" If you have verified that {number} is the local emergency number, you may use it."
    return SafetyCheckResult(
        possible_emergency=possible,
        matched_signs=matched,
        warning_message=warning if possible else "",
        urdu_warning_message=URDU_EMERGENCY_BODY if possible else "",
        emergency_number=number,
    )


def apply_conservative_urgency(model_urgency: str, safety: SafetyCheckResult) -> str:
    """Force EMERGENCY when the safety scan already found warning signs."""
    return safety.overlay_urgency(model_urgency)


def get_emergency_banner_text(language: str = "English") -> str:
    """Return a prominent, human-written emergency notice. Not model output."""
    if language == "Urdu":
        return f"{EMERGENCY_BODY}\n\n{URDU_EMERGENCY_BODY}"
    return EMERGENCY_BODY
