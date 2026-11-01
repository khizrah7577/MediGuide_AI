"""
Clinic sidebar: navigation, language, cache, and disclaimer.
"""

from __future__ import annotations

import streamlit as st

from src.cache_manager import apply_cache, cache_privacy_notice, clear_cache, get_active_mode
from src.config import (
    APP_NAME,
    CACHE_MODE_DISABLED,
    CACHE_MODE_MEMORY,
    CACHE_MODE_SQLITE,
    MEDICAL_DISCLAIMER,
    PAGE_ASSESSMENT,
    PAGE_CHAT,
    PAGE_DEMO,
    PAGE_HISTORY,
    PAGE_HOME,
    PAGE_LABELS,
    PAGE_RESULTS,
    PAGE_SETTINGS,
    PROJECT_ROOT,
    has_api_key,
)
from ui.login_page import sign_out
from ui.styles import LOGO_SVG


def render_sidebar() -> str:
    """Draw the clinic sidebar and return the selected page key."""
    logo_path = PROJECT_ROOT / "assets" / "logo.svg"
    if logo_path.exists():
        st.logo(str(logo_path), size="large")

    with st.sidebar:
        st.markdown(
            f"<div style='display:flex;gap:10px;align-items:center;margin-bottom:0.35rem;'>"
            f"<div>{LOGO_SVG}</div><div><strong>{APP_NAME}</strong><br/>"
            f"<span style='color:#99F6E4;font-size:0.82rem;'>Clinic chatbot</span></div></div>",
            unsafe_allow_html=True,
        )
        st.caption("Understand your symptoms. Explore your next steps.")

        pages = [
            PAGE_HOME,
            PAGE_CHAT,
            PAGE_ASSESSMENT,
            PAGE_RESULTS,
            PAGE_HISTORY,
            PAGE_SETTINGS,
            PAGE_DEMO,
        ]
        labels = [PAGE_LABELS[key] for key in pages]
        current = st.session_state.get("current_page", PAGE_HOME)
        if current not in pages:
            current = PAGE_HOME
        selected_label = st.radio(
            "Clinic navigation",
            labels,
            index=pages.index(current),
        )
        selected = pages[labels.index(selected_label)]
        st.session_state.current_page = selected

        st.caption("Visit status")
        visitor = st.session_state.get("visitor_name") or "Clinic visitor"
        st.caption(f"Signed in as {visitor}")
        if st.session_state.get("key_verified_live"):
            st.badge("API key verified", icon=":material/check_circle:", color="green")
        else:
            st.badge("API key in session", icon=":material/key:", color="blue")
        if st.button("Sign out", icon=":material/logout:", width="stretch"):
            sign_out()

        st.session_state.default_language = st.selectbox(
            "Default reply language",
            ("English", "Urdu"),
            index=0 if st.session_state.get("default_language", "English") == "English" else 1,
            help="The chat and form can override this. Emergency warnings stay prominent.",
        )

        with st.expander("Cache and privacy"):
            cache_labels = {
                CACHE_MODE_DISABLED: "Off (recommended)",
                CACHE_MODE_MEMORY: "In-memory cache",
                CACHE_MODE_SQLITE: "SQLite cache",
            }
            requested_mode = st.selectbox(
                "LLM cache",
                list(cache_labels.keys()),
                format_func=lambda key: cache_labels[key],
                index=["disabled", "memory", "sqlite"].index(
                    st.session_state.get("cache_mode", CACHE_MODE_DISABLED)
                ),
            )
            if requested_mode != get_active_mode():
                mode, message = apply_cache(requested_mode)
                st.session_state.cache_mode = mode
                st.session_state.cache_status = message
            st.caption(f"Active cache: {get_active_mode()}")
            if st.button("Clear cache", width="stretch"):
                st.session_state.cache_status = clear_cache()
                st.session_state.cache_mode = get_active_mode()
            if st.session_state.get("cache_status"):
                st.caption(st.session_state.cache_status)
            st.caption(cache_privacy_notice())

        st.markdown(
            f"<div class='mg-disclaimer' style='font-size:0.78rem;'>{MEDICAL_DISCLAIMER}</div>",
            unsafe_allow_html=True,
        )
    return st.session_state.current_page
