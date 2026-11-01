"""
MediGuide AI — application entry point.

Launch:
    python -m streamlit run app.py

Students: this file starts Streamlit, prepares session state,
shows the sidebar, and opens the selected page. The medical
logic lives in src/, and the visual pieces live in ui/.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.cache_manager import apply_cache
from src.config import (
    APP_NAME,
    CACHE_MODE_DISABLED,
    PAGE_ASSESSMENT,
    PAGE_CHAT,
    PAGE_DEMO,
    PAGE_HISTORY,
    PAGE_HOME,
    PAGE_RESULTS,
    PAGE_SETTINGS,
    cache_enabled_by_env,
    clear_runtime_api_key,
    history_enabled_by_env,
)
from src.prompts import get_message_demonstration
from ui.assessment_form import render_assessment_form
from ui.chat_page import render_chat_page
from ui.components import disclaimer_box, render_home_page, render_page_intro
from ui.history_page import render_history_page
from ui.login_page import render_login_page
from ui.results_dashboard import render_results_dashboard
from ui.settings_page import render_settings_page
from ui.sidebar import render_sidebar
from ui.styles import inject_styles

SESSION_DEFAULTS = {
    "current_page": PAGE_HOME,
    "history_enabled": history_enabled_by_env(),
    "cache_mode": "memory" if cache_enabled_by_env() else CACHE_MODE_DISABLED,
    "cache_status": "",
    "default_language": "English",
    "last_outcome": None,
    "last_submission_hash": None,
    "streamed_explanation": None,
    "assessment_in_progress": False,
    "emergency_alert": None,
    "openai_api_key_override": "",
    "model_name_override": "",
    "chat_assessment_done": False,
    "clinic_logged_in": False,
    "visitor_name": "",
    "login_status": "",
    "key_verified_live": False,
}


def init_session_state() -> None:
    """Create session keys once so later pages never read missing values."""
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_session_overrides() -> None:
    """Copy Settings page values into environment variables for this process."""
    key = (st.session_state.get("openai_api_key_override") or "").strip()
    if key:
        os.environ["OPENAI_API_KEY"] = key
    model = (st.session_state.get("model_name_override") or "").strip()
    if model:
        os.environ["OPENAI_MODEL"] = model
    if st.session_state.get("temperature_override") is not None:
        os.environ["OPENAI_TEMPERATURE"] = str(st.session_state.temperature_override)
    if st.session_state.get("timeout_override") is not None:
        os.environ["OPENAI_TIMEOUT_SECONDS"] = str(int(st.session_state.timeout_override))


def render_langchain_demo() -> None:
    """Labelled teaching page for SystemMessage, HumanMessage, and AIMessage."""
    render_page_intro(
        "LangChain message demonstration",
        "A teaching example of SystemMessage, HumanMessage, and AIMessage. This is not a live medical result.",
        icon=":material/school:",
    )
    st.info(
        "This page is an educational demo of LangChain message objects. "
        "The assistant text below is a fixed teaching example. "
        "It is not a live model-generated medical assessment.",
        icon=":material/info:",
    )
    for message in get_message_demonstration():
        role = message.__class__.__name__.replace("Message", "").lower()
        avatar = ":material/stethoscope:" if role == "ai" else (
            ":material/person:" if role == "human" else ":material/policy:"
        )
        with st.chat_message("assistant" if role == "ai" else "user" if role == "human" else "assistant", avatar=avatar):
            st.caption(message.__class__.__name__)
            st.write(message.content)
    st.caption(
        "In the real assessment, ChatPromptTemplate builds messages like these, "
        "LLMChain asks the model for JSON, and a second stream() call writes the explanation."
    )
    disclaimer_box()


def main() -> None:
    st.set_page_config(
        page_title=APP_NAME,
        page_icon=":material/stethoscope:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_session_state()

    if not st.session_state.get("clinic_logged_in"):
        # Runtime login: the OpenAI key is typed here, not read from a saved file.
        clear_runtime_api_key()
        render_login_page()
        return

    inject_styles()
    apply_session_overrides()

    # Register the selected LangChain cache without repeating work on every rerun.
    apply_cache(st.session_state.get("cache_mode", CACHE_MODE_DISABLED))

    page = render_sidebar()
    # Page body is chosen from the clinic navigation.

    if page == PAGE_HOME:
        render_home_page()
    elif page == PAGE_CHAT:
        render_chat_page()
    elif page == PAGE_ASSESSMENT:
        render_assessment_form()
    elif page == PAGE_RESULTS:
        render_results_dashboard()
    elif page == PAGE_HISTORY:
        render_history_page()
    elif page == PAGE_SETTINGS:
        render_settings_page()
    elif page == PAGE_DEMO:
        render_langchain_demo()
    else:
        render_home_page()


if __name__ == "__main__":
    main()
