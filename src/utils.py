"""
Small helper functions used across MediGuide AI.

Students: keep generic helpers here so validation, chains,
and the UI do not copy-paste the same code.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

# Matches ```json ... ``` or ``` ... ``` fences that models sometimes add.
_FENCE_PATTERN = re.compile(
    r"^\s*```(?:json|JSON)?\s*(.*?)\s*```\s*$",
    re.DOTALL,
)

# Extra fence cleanup when the model wraps JSON but also adds text around it.
_INNER_FENCE_PATTERN = re.compile(
    r"```(?:json|JSON)?\s*(.*?)\s*```",
    re.DOTALL,
)


def setup_logger(name: str = "mediguide") -> logging.Logger:
    """
    Create a logger that writes useful technical messages.

    Important: never log patient notes, medications, symptoms, or API keys.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


LOGGER = setup_logger()


def utc_now_iso() -> str:
    """Return the current UTC time in ISO format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def format_display_datetime(iso_value: str | None) -> str:
    """Turn an ISO timestamp into a friendlier local display string."""
    if not iso_value:
        return "Unknown time"
    try:
        parsed = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return iso_value


def new_assessment_id() -> str:
    """Create a unique ID for one assessment. This is not a patient account ID."""
    return uuid.uuid4().hex


def strip_markdown_fences(raw_text: str) -> str:
    """
    Remove Markdown code fences from a model response.

    Example:
        ```json
        {"summary": "..."}
        ```
    becomes
        {"summary": "..."}
    """
    if not raw_text:
        return ""
    text = raw_text.strip()
    fenced = _FENCE_PATTERN.match(text)
    if fenced:
        return fenced.group(1).strip()
    inner = _INNER_FENCE_PATTERN.search(text)
    if inner:
        return inner.group(1).strip()
    return text


def extract_json_object(text: str) -> str:
    """
    If the model added extra sentences around JSON, keep the first {...} block.
    """
    if not text:
        return ""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return text.strip()
    return text[start : end + 1].strip()


def parse_json_safely(raw_text: str) -> tuple[dict[str, Any] | None, str | None]:
    """
    Parse JSON without using eval().

    Returns (data, error_message).
    data is None when parsing fails.
    """
    if raw_text is None:
        return None, "The model returned an empty response."

    cleaned = strip_markdown_fences(str(raw_text))
    if not cleaned.strip():
        return None, "The model returned an empty response."

    candidate = extract_json_object(cleaned)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None, (
            "The AI response was not valid JSON. "
            "You can try generating the assessment again."
        )

    if not isinstance(parsed, dict):
        return None, "The AI response was JSON, but it was not an object with fields."
    return parsed, None


def format_symptom_list(symptoms: list[str], free_text: str = "") -> str:
    """Join selected symptoms and optional free-text into one readable string."""
    parts = [item.strip() for item in symptoms if item and item.strip()]
    extra = (free_text or "").strip()
    if extra:
        parts.append(extra)
    return ", ".join(parts) if parts else "Not provided"


def compact_text(value: str | None, fallback: str = "Not provided") -> str:
    """Return trimmed text, or a fallback when the user left a field empty."""
    text = (value or "").strip()
    return text if text else fallback


def fingerprint_payload(payload: dict[str, Any]) -> str:
    """
    Build a stable hash of form values.

    Used only to detect accidental duplicate submissions in one session.
    Hashing does not make cached medical data private.
    """
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def chunk_text_from_message(chunk: Any) -> str:
    """Extract text from a LangChain streaming chunk."""
    if chunk is None:
        return ""
    content = getattr(chunk, "content", chunk)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
        return "".join(parts)
    return str(content) if content else ""
