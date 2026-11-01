"""
Settings: model, privacy, cache, and history options.
"""

from __future__ import annotations

import os

import streamlit as st

from src.cache_manager import apply_cache, cache_privacy_notice, clear_cache, get_active_mode
from src.config import (
    CACHE_MODE_DISABLED,
    CACHE_MODE_MEMORY,
    CACHE_MODE_SQLITE,
    DEFAULT_MODEL,
    get_model_name,
    get_temperature,
    get_timeout_seconds,
    has_api_key,
)
from ui.components import disclaimer_box, render_page_intro
from ui.login_page import sign_out


def render_settings_page() -> None:
    render_page_intro(
        "Clinic settings",
        "Model access, privacy choices, and cache controls for this educational prototype.",
        icon=":material/settings:",
    )
    disclaimer_box()

    st.subheader("OpenAI configuration")
    st.write(
        "Live assessment uses the OpenAI API through LangChain ChatOpenAI. "
        "A ChatGPT subscription does **not** automatically include API credits. "
        "You need an API key from the OpenAI platform."
    )
    if has_api_key() or st.session_state.get("openai_api_key_override"):
        st.success("You are signed in with a session API key. The key is never displayed.", icon=":material/check_circle:")
    else:
        st.warning("No API key is in this session. Sign out and enter a key on the login page.", icon=":material/key:")

    override = st.text_input(
        "Replace the session API key",
        type="password",
        help="This value stays in Streamlit session state. It is not written to disk by the app.",
        value="",
    )
    if override.strip():
        st.session_state.openai_api_key_override = override.strip()
        os.environ["OPENAI_API_KEY"] = override.strip()
        st.success("Session API key updated in memory. It will be lost when you sign out or close the app.", icon=":material/check_circle:")

    if st.button("Sign out of clinic", icon=":material/logout:"):
        sign_out()

    st.session_state.model_name_override = st.text_input(
        "Model name",
        value=st.session_state.get("model_name_override") or get_model_name() or DEFAULT_MODEL,
        help="Example: gpt-4o-mini. Your account must actually have access to this model.",
    )
    os.environ["OPENAI_MODEL"] = st.session_state.model_name_override

    current_temperature = st.session_state.get("temperature_override")
    if current_temperature is None:
        current_temperature = get_temperature()
    st.session_state.temperature_override = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=float(current_temperature),
        help="Lower values keep answers more consistent. This is not a medical accuracy control.",
    )
    current_timeout = st.session_state.get("timeout_override")
    if current_timeout is None:
        current_timeout = get_timeout_seconds()
    st.session_state.timeout_override = st.number_input(
        "Timeout (seconds)",
        min_value=10,
        max_value=180,
        value=int(current_timeout),
    )
    os.environ["OPENAI_TEMPERATURE"] = str(st.session_state.temperature_override)
    os.environ["OPENAI_TIMEOUT_SECONDS"] = str(int(st.session_state.timeout_override))

    st.subheader("Privacy")
    st.write(
        "This educational prototype does not create secure individual patient accounts. "
        "Anyone with access to this computer could open local files in the data folder. "
        "Do not use it for real identifiable patient records."
    )
    st.session_state.history_enabled = st.toggle(
        "Save assessment history locally",
        value=bool(st.session_state.get("history_enabled", False)),
    )
    st.caption(
        "History can store age, gender, symptoms, duration, severity, language, "
        "urgency, and educational JSON. Medications and additional notes are not stored."
    )

    st.subheader("LLM cache")
    st.write(cache_privacy_notice())
    labels = {
        CACHE_MODE_DISABLED: "Disabled (recommended)",
        CACHE_MODE_MEMORY: "In-memory (lost when the app stops)",
        CACHE_MODE_SQLITE: "SQLite file in the data folder (can persist)",
    }
    choice = st.radio(
        "Cache mode",
        list(labels.keys()),
        format_func=lambda key: labels[key],
        index=["disabled", "memory", "sqlite"].index(st.session_state.get("cache_mode", CACHE_MODE_DISABLED)),
    )
    if choice != st.session_state.get("cache_mode"):
        mode, message = apply_cache(choice)
        st.session_state.cache_mode = mode
        st.session_state.cache_status = message
        st.info(message, icon=":material/info:")
    st.caption(f"Currently active: {get_active_mode()}")
    if st.button("Clear LLM cache now", icon=":material/delete:"):
        st.session_state.cache_status = clear_cache()
        st.session_state.cache_mode = get_active_mode()
        st.success(st.session_state.cache_status, icon=":material/check_circle:")

    st.subheader("What is stored where")
    st.markdown(
        """
        - **Session state:** current form values, chat messages, and the latest result, until the browser session ends.
        - **Optional SQLite history:** selected assessment fields, if you enable history.
        - **Optional LLM cache:** model inputs and outputs, if you enable cache.
        - **Never logged:** medications, extra notes, and API keys.
        """
    )
