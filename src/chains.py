"""
LangChain model wiring for MediGuide AI.

This file demonstrates:
- ChatOpenAI
- LLMChain (used in the real assessment workflow)
- SystemMessage / HumanMessage / AIMessage
- Genuine model streaming with .stream()

Architecture note:
The structured JSON and the streamed explanation are TWO model calls.
The dashboard never claims they came from a single request.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from src.config import get_model_name, get_openai_api_key, get_temperature, get_timeout_seconds
from src.prompts import (
    ASSESSMENT_CHAT_PROMPT,
    CHAT_FOLLOWUP_PROMPT,
    EXPLANATION_CHAT_PROMPT,
    get_assessment_prompt_variables,
    get_message_demonstration,
)
from src.utils import LOGGER, chunk_text_from_message

# LLMChain is required by the assignment. It is deprecated in LangChain 0.3
# in favour of LCEL (prompt | llm), but we still use it so the project
# matches the required concepts. A tiny fallback is included if the
# installed LangChain version no longer exports LLMChain.
try:
    from langchain.chains import LLMChain
except ImportError:  # pragma: no cover - only used on newer LangChain lines
    class LLMChain:  # type: ignore[no-redef]
        """Minimal stand-in that keeps the same invoke() shape as LLMChain."""

        def __init__(self, llm, prompt, verbose: bool = False):
            self.llm = llm
            self.prompt = prompt
            self.verbose = verbose

        def invoke(self, inputs: dict[str, Any]) -> dict[str, str]:
            messages = self.prompt.format_messages(**inputs)
            response = self.llm.invoke(messages)
            content = getattr(response, "content", str(response))
            return {"text": content}


class MissingAPIKeyError(RuntimeError):
    """Raised when the app would otherwise send a request without a key."""


def build_chat_openai(
    *,
    api_key: str | None = None,
    model_name: str | None = None,
    temperature: float | None = None,
    timeout: int | None = None,
    streaming: bool = False,
) -> ChatOpenAI:
    """
    Create a ChatOpenAI client.

    ChatOpenAI is LangChain's chat-model wrapper around OpenAI chat models.
    """
    key = (api_key if api_key is not None else get_openai_api_key()).strip()
    if not key:
        raise MissingAPIKeyError(
            "Live AI assessment needs an OpenAI API key. "
            "Sign in on the clinic login page with your key. "
            "A ChatGPT subscription does not automatically include API credits."
        )
    return ChatOpenAI(
        api_key=key,
        model=model_name or get_model_name(),
        temperature=get_temperature() if temperature is None else temperature,
        timeout=get_timeout_seconds() if timeout is None else timeout,
        streaming=streaming,
        max_retries=1,
    )


def build_assessment_chain(llm: Any | None = None) -> LLMChain:
    """
    Build the LLMChain used by the real assessment workflow.

    LLMChain connects a prompt template to a chat model and returns text.
    """
    chat_model = llm if llm is not None else build_chat_openai()
    return LLMChain(
        llm=chat_model,
        prompt=ASSESSMENT_CHAT_PROMPT,
        verbose=False,
    )


def run_structured_assessment(
    patient_variables: dict[str, Any],
    llm: Any | None = None,
) -> str:
    """
    Run the JSON assessment through LLMChain.

    Returns the raw text from the model. Parsing happens in utils/validation.
    """
    chain = build_assessment_chain(llm=llm)
    variables = get_assessment_prompt_variables(patient_variables)
    output = chain.invoke(variables)
    return _extract_chain_text(output)


def _extract_chain_text(output: Any) -> str:
    if output is None:
        return ""
    if isinstance(output, str):
        return output
    if isinstance(output, dict):
        for key in ("text", "content", "output"):
            if key in output and output[key]:
                return str(output[key])
        return str(output)
    content = getattr(output, "content", None)
    if content:
        return str(content)
    return str(output)


def stream_educational_explanation(
    patient_variables: dict[str, Any],
    structured_json: str,
    llm: Any | None = None,
) -> Iterator[str]:
    """
    Genuine token streaming for the educational explanation.

    This is a second model call, separate from the JSON LLMChain call.
    The generator yields text pieces for Streamlit's st.write_stream().
    """
    chat_model = llm if llm is not None else build_chat_openai(streaming=True)
    messages = EXPLANATION_CHAT_PROMPT.format_messages(
        symptoms=patient_variables.get("symptoms", ""),
        duration=patient_variables.get("duration", ""),
        severity=patient_variables.get("severity", ""),
        response_language=patient_variables.get("response_language", "English"),
        structured_json=structured_json,
    )
    for chunk in chat_model.stream(messages):
        piece = chunk_text_from_message(chunk)
        if piece:
            yield piece


def stream_chat_followup(
    *,
    user_message: str,
    conversation: str,
    prior_summary: str,
    response_language: str = "English",
    llm: Any | None = None,
) -> Iterator[str]:
    """
    Genuine token streaming for a clinic-chat follow-up.

    This is a separate model call from the JSON assessment and from
    the educational explanation stream.
    """
    from src.config import MEDICAL_DISCLAIMER

    chat_model = llm if llm is not None else build_chat_openai(streaming=True)
    messages = CHAT_FOLLOWUP_PROMPT.format_messages(
        disclaimer=MEDICAL_DISCLAIMER,
        response_language=response_language or "English",
        prior_summary=prior_summary or "No previous educational summary is available.",
        conversation=conversation or "(no earlier chat)",
        user_message=user_message,
    )
    for chunk in chat_model.stream(messages):
        piece = chunk_text_from_message(chunk)
        if piece:
            yield piece


def classify_llm_error(exc: Exception) -> str:
    """
    Convert technical API errors into friendly user-facing sentences.

    Do not include the original payload; it may contain patient text.
    """
    name = type(exc).__name__.lower()
    text = str(exc).lower()

    if isinstance(exc, MissingAPIKeyError):
        return str(exc)
    if "authentication" in name or "unauthorized" in text or "invalid api key" in text or "api key" in text:
        return (
            "The OpenAI API key looks missing or invalid. "
            "Sign out and enter a valid key on the login page. "
            "Do not share that key with anyone."
        )
    if "rate" in text or "429" in text:
        return "The model is temporarily busy (rate limit). Please wait a moment and try again."
    if "timeout" in name or "timeout" in text:
        return "The AI request timed out. Please try again. If this keeps happening, increase OPENAI_TIMEOUT_SECONDS."
    if "connect" in text or "network" in text or "connection" in name:
        return "A network problem stopped the AI request. Check your internet connection and try again."
    if "not found" in text or "does not exist" in text or "model" in text and "unavailable" in text:
        return (
            "The configured model is not available for this API key. "
            "Try another model name in Settings, such as gpt-4o-mini, if your account supports it."
        )
    if "empty" in text:
        return "The model returned an empty response. Please try again."
    LOGGER.warning("Unexpected LLM error type=%s", type(exc).__name__)
    return "The AI service could not complete this request. Please try again in a moment."


def demonstration_messages() -> list[BaseMessage]:
    """Return the labelled educational message objects for the UI demo page."""
    return get_message_demonstration()
