"""
Application configuration for MediGuide AI.

Students: this file is the control panel of the project.
It reads environment variables, stores constants, and
gives the rest of the app one place to look for settings.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root = the folder that contains app.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ENV_PATH = PROJECT_ROOT / ".env"

# Load .env if it exists. Missing .env is allowed so the home page still opens.
load_dotenv(dotenv_path=ENV_PATH, override=False)

# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------
APP_NAME = "MediGuide AI"
APP_FULL_TITLE = "AI-Powered Medical Symptom Assessment and Patient Guidance Assistant"
APP_TAGLINE = "Understand your symptoms. Explore your next steps."

# This exact disclaimer must appear on the home, assessment, sidebar, and results pages.
MEDICAL_DISCLAIMER = (
    "MEDICAL DISCLAIMER: MediGuide AI is an educational AI prototype. It does "
    "not provide a medical diagnosis and is not a substitute for a licensed "
    "healthcare professional, medical examination, emergency service, or "
    "treatment. Consult a qualified healthcare professional for medical "
    "concerns. If you may be experiencing a medical emergency, seek emergency "
    "help immediately."
)

EDUCATIONAL_ONLY_NOTICE = (
    "This application is an educational prototype. It is not a diagnostic "
    "tool, medical device, or replacement for a doctor's examination."
)

# ---------------------------------------------------------------------------
# OpenAI / LangChain model settings
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TIMEOUT_SECONDS = 60


def _as_bool(value: str | None, default: bool = False) -> bool:
    """Convert common environment text values into a boolean."""
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_float(value: str | None, default: float) -> float:
    try:
        return float(value) if value not in (None, "") else default
    except ValueError:
        return default


def _as_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except ValueError:
        return default


def get_openai_api_key() -> str:
    """Return the API key from the environment. Never hard-code a key."""
    return (os.getenv("OPENAI_API_KEY") or "").strip()


def has_api_key() -> bool:
    """True when a non-empty OpenAI API key is configured."""
    return bool(get_openai_api_key())


def apply_runtime_api_key(key: str, model_name: str | None = None) -> None:
    """Store a user-typed key in this process only. Never write it to disk."""
    os.environ["OPENAI_API_KEY"] = (key or "").strip()
    if model_name and model_name.strip():
        os.environ["OPENAI_MODEL"] = model_name.strip()


def clear_runtime_api_key() -> None:
    """Remove the runtime key so the next visitor must sign in again."""
    os.environ.pop("OPENAI_API_KEY", None)


def get_model_name() -> str:
    return (os.getenv("OPENAI_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL


def get_temperature() -> float:
    return _as_float(os.getenv("OPENAI_TEMPERATURE"), DEFAULT_TEMPERATURE)


def get_timeout_seconds() -> int:
    return max(10, _as_int(os.getenv("OPENAI_TIMEOUT_SECONDS"), DEFAULT_TIMEOUT_SECONDS))


def history_enabled_by_env() -> bool:
    return _as_bool(os.getenv("ENABLE_ASSESSMENT_HISTORY"), False)


def cache_enabled_by_env() -> bool:
    return _as_bool(os.getenv("ENABLE_LLM_CACHE"), False)


def get_local_emergency_number() -> str:
    """
    Return a user-configured emergency number, or an empty string.

    We never invent a phone number. A number is shown only when the
    user (or instructor) has explicitly set LOCAL_EMERGENCY_NUMBER.
    """
    return (os.getenv("LOCAL_EMERGENCY_NUMBER") or "").strip()


# ---------------------------------------------------------------------------
# Paths for optional on-disk features
# ---------------------------------------------------------------------------
HISTORY_DB_PATH = DATA_DIR / "assessment_history.sqlite"
LLM_CACHE_DB_PATH = DATA_DIR / "langchain_cache.sqlite"

# Cache modes used by src/cache_manager.py and the Settings page.
CACHE_MODE_DISABLED = "disabled"
CACHE_MODE_MEMORY = "memory"
CACHE_MODE_SQLITE = "sqlite"
CACHE_MODES = (CACHE_MODE_DISABLED, CACHE_MODE_MEMORY, CACHE_MODE_SQLITE)

# ---------------------------------------------------------------------------
# Form options
# ---------------------------------------------------------------------------
AGE_MIN = 0
AGE_MAX = 120
SEVERITY_MIN = 1
SEVERITY_MAX = 10

GENDER_OPTIONS = (
    "Prefer not to say",
    "Female",
    "Male",
    "Non-binary",
    "Another identity",
)

COMMON_SYMPTOMS = (
    "Fever",
    "Headache",
    "Cough",
    "Sore throat",
    "Runny nose",
    "Fatigue",
    "Nausea",
    "Vomiting",
    "Dizziness",
    "Abdominal pain",
    "Chest pain",
    "Shortness of breath",
    "Muscle pain",
    "Joint pain",
    "Skin rash",
    "Diarrhea",
    "Constipation",
    "Other",
)

DURATION_OPTIONS = (
    "Less than 24 hours",
    "1–3 days",
    "4–7 days",
    "1–2 weeks",
    "More than 2 weeks",
    "Unsure",
)

RESPONSE_LANGUAGES = ("English", "Urdu")

ONSET_OPTIONS = (
    "Unsure",
    "Gradual",
    "Sudden",
)

PREGNANCY_OPTIONS = (
    "Prefer not to say",
    "Not applicable",
    "Not pregnant",
    "Possibly pregnant",
    "Pregnant",
    "Postpartum",
)

SMOKING_OPTIONS = (
    "Prefer not to say",
    "Never",
    "Former",
    "Occasional",
    "Daily",
)

SLEEP_OPTIONS = (
    "Prefer not to say",
    "Well",
    "Fair",
    "Poor",
    "Almost none",
)

TRAVEL_OPTIONS = (
    "Prefer not to say",
    "No recent travel",
    "Recent local travel",
    "Recent international travel",
)

CONTACT_OPTIONS = (
    "Unsure",
    "No known contact with a sick person",
    "Yes, recent contact with a sick person",
)

BLOOD_GROUP_OPTIONS = (
    "Unknown / prefer not to say",
    "A+",
    "A-",
    "B+",
    "B-",
    "AB+",
    "AB-",
    "O+",
    "O-",
)

ACTIVITY_IMPACT_OPTIONS = (
    "Prefer not to say",
    "I can do usual activities",
    "A little limited",
    "Clearly limited",
    "I am mostly resting",
)

ALLOWED_URGENCY_LEVELS = ("LOW", "MEDIUM", "HIGH", "EMERGENCY")

# ---------------------------------------------------------------------------
# Navigation page keys
# ---------------------------------------------------------------------------
PAGE_HOME = "home"
PAGE_CHAT = "chat"
PAGE_ASSESSMENT = "assessment"
PAGE_RESULTS = "results"
PAGE_HISTORY = "history"
PAGE_SETTINGS = "settings"
PAGE_DEMO = "langchain_demo"

PAGE_LABELS = {
    PAGE_HOME: ":material/home: Clinic home",
    PAGE_CHAT: ":material/stethoscope: Medical chat",
    PAGE_ASSESSMENT: ":material/assignment: Symptom form",
    PAGE_RESULTS: ":material/clinical_notes: Results",
    PAGE_HISTORY: ":material/history: History",
    PAGE_SETTINGS: ":material/settings: Settings",
    PAGE_DEMO: ":material/school: LangChain demo",
}


def ensure_data_dir() -> Path:
    """Create the data folder if it does not exist yet."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR
