"""
Reusable Streamlit UI pieces: clinic headers, cards, disclaimers, and notices.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.config import (
    APP_FULL_TITLE,
    APP_NAME,
    APP_TAGLINE,
    EDUCATIONAL_ONLY_NOTICE,
    MEDICAL_DISCLAIMER,
    PAGE_ASSESSMENT,
    PAGE_CHAT,
    PAGE_HISTORY,
    PAGE_SETTINGS,
    has_api_key,
)
from ui.styles import LOGO_SVG


def render_brand_header(subtitle: str | None = None) -> None:
    title = subtitle or APP_FULL_TITLE
    st.markdown(
        f"""
        <div class="mg-hero">
            <div class="mg-logo-row">
                <div class="mg-mark">{LOGO_SVG}</div>
                <div>
                    <div class="mg-kicker">Educational clinic assistant</div>
                    <h1>{APP_NAME}</h1>
                    <p>{APP_TAGLINE}</p>
                </div>
            </div>
        </div>
        <p class="mg-muted">{title}</p>
        """,
        unsafe_allow_html=True,
    )


def render_page_intro(title: str, body: str, icon: str = ":material/stethoscope:") -> None:
    """Compact inner-page heading used on chat, form, history, and settings."""
    st.header(f"{icon} {title}")
    st.caption(body)


def disclaimer_box() -> None:
    st.markdown(
        f'<div class="mg-disclaimer"><strong>Medical disclaimer</strong><br/>{MEDICAL_DISCLAIMER}</div>',
        unsafe_allow_html=True,
    )


def educational_note() -> None:
    st.caption(EDUCATIONAL_ONLY_NOTICE)


def emergency_banner(message: str, extra: str = "") -> None:
    extra_html = f"<p>{extra}</p>" if extra else ""
    st.markdown(
        f"""
        <div class="mg-emergency">
            <h3>Possible emergency warning</h3>
            <p>{message}</p>
            {extra_html}
            <p><strong>This warning is shown by the application itself. It does not wait for the AI.</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_card(title: str, body: str) -> None:
    with st.container(border=True):
        st.subheader(title)
        st.write(body)


def urgency_pill(level: str) -> str:
    mapping = {
        "LOW": ("mg-pill-low", "LOW — educational label only, not a safety guarantee"),
        "MEDIUM": ("mg-pill-medium", "MEDIUM — caution, discuss with a clinician"),
        "HIGH": ("mg-pill-high", "HIGH — seek prompt medical advice"),
        "EMERGENCY": ("mg-pill-emergency", "EMERGENCY — seek emergency care now"),
    }
    css, label = mapping.get(level, ("mg-pill-medium", level or "Unknown"))
    return f'<span class="mg-pill {css}">{label}</span>'


def show_urgency_badge(level: str) -> None:
    """Native badge plus a text label so colour is never the only signal."""
    level = (level or "").upper()
    colors = {
        "LOW": "green",
        "MEDIUM": "orange",
        "HIGH": "orange",
        "EMERGENCY": "red",
    }
    labels = {
        "LOW": "Low — educational label only",
        "MEDIUM": "Medium — caution",
        "HIGH": "High — seek prompt advice",
        "EMERGENCY": "Emergency — seek care now",
    }
    st.badge(
        labels.get(level, level or "Unknown"),
        icon=":material/monitor_heart:",
        color=colors.get(level, "gray"),
    )


def render_clinic_status_chips() -> None:
    key_ready = has_api_key() or bool(st.session_state.get("openai_api_key_override"))
    history_on = bool(st.session_state.get("history_enabled"))
    st.markdown(
        f"""
        <div class="mg-clinic-strip">
            <span class="mg-chip">Educational prototype</span>
            <span class="mg-chip">{"AI chat ready" if key_ready else "AI key not set"}</span>
            <span class="mg-chip">{"History on" if history_on else "History off"}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_structured_chat_cards(structured: dict[str, Any]) -> None:
    """Show JSON assessment fields inside a clinic chat bubble."""
    if not structured:
        return
    show_urgency_badge(str(structured.get("urgency_level") or ""))
    if structured.get("summary"):
        st.write(structured["summary"])
    conditions = structured.get("possible_conditions") or []
    if conditions:
        with st.expander("Possible conditions to discuss"):
            st.caption("These are possibilities only. They are not confirmed diagnoses.")
            for item in conditions:
                st.markdown(f"**{item.get('name') or 'Unnamed possibility'}**")
                st.write(item.get("reason") or "")
    steps = structured.get("recommended_next_steps") or []
    if steps:
        with st.expander("Suggested next steps"):
            for step in steps:
                st.markdown(f"- {step}")
    questions = structured.get("questions_for_doctor") or []
    if questions:
        with st.expander("Questions for a healthcare professional"):
            for question in questions:
                st.markdown(f"- {question}")
    warnings = structured.get("warning_signs") or []
    if warnings:
        with st.expander("Warning signs"):
            for warning in warnings:
                st.markdown(f"- {warning}")


def render_home_page() -> None:
    """Clinic home. Must load even when no API key is configured."""
    render_brand_header()
    render_clinic_status_chips()
    disclaimer_box()

    visitor = st.session_state.get("visitor_name")
    if visitor:
        st.subheader(f"Welcome, {visitor}")
    else:
        st.subheader("Welcome to the MediGuide clinic desk")
    st.write(
        "MediGuide AI is a **professional educational chatbot** that helps you "
        "describe symptoms in an organised way and review **general health "
        "information** you can take to a qualified healthcare professional. "
        "It does not examine you, test you, or confirm a disease."
    )

    with st.container(horizontal=True):
        if st.button(
            "Open medical chat",
            type="primary",
            icon=":material/stethoscope:",
            width="stretch",
        ):
            st.session_state.current_page = PAGE_CHAT
            st.rerun()
        if st.button(
            "Use guided form",
            icon=":material/assignment:",
            width="stretch",
        ):
            st.session_state.current_page = PAGE_ASSESSMENT
            st.rerun()

    st.caption("No login is required. This prototype is for education and coursework.")

    st.subheader("How a visit works")
    col_a, col_b, col_c = st.columns(3)
    steps = [
        ("1", "Describe symptoms", "Chat in everyday language, or fill the guided form."),
        ("2", "Review general information", "The assistant may share educational next-step ideas."),
        ("3", "Talk to a professional", "Use the summary and questions with a qualified clinician."),
    ]
    for column, (number, title, body) in zip((col_a, col_b, col_c), steps):
        with column:
            st.markdown(
                f"""
                <div class="mg-step">
                    <div class="mg-step-number">{number}</div>
                    <h4>{title}</h4>
                    <p>{body}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.subheader("What this assistant is — and is not")
    st.info(
        "This is an educational AI prototype for a university project. "
        "It is not a diagnostic tool, not a medical device, and not emergency care. "
        "It does not claim medical accuracy percentages.",
        icon=":material/info:",
    )

    if not has_api_key() and not st.session_state.get("openai_api_key_override"):
        st.warning(
            "Live AI chat is not configured yet. You can still explore the clinic "
            "home, form, history, and settings. Add an OpenAI API key in Settings "
            "or in a local .env file to generate model-based information.",
            icon=":material/key:",
        )

    with st.container(horizontal=True):
        if st.button("Open history", icon=":material/history:", width="stretch"):
            st.session_state.current_page = PAGE_HISTORY
            st.rerun()
        if st.button("Open settings", icon=":material/settings:", width="stretch"):
            st.session_state.current_page = PAGE_SETTINGS
            st.rerun()

    educational_note()
