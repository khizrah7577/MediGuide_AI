"""
Runtime clinic login.

The visitor pastes an OpenAI API key here. The key stays in Streamlit
session memory for this browser visit. It is not written to disk and
is not a secure patient account.
"""

from __future__ import annotations

import streamlit as st

from src.config import (
    APP_NAME,
    APP_TAGLINE,
    DEFAULT_MODEL,
    MEDICAL_DISCLAIMER,
    apply_runtime_api_key,
    get_model_name,
)
from src.validation import looks_like_openai_api_key
from ui.styles import LOGO_SVG, inject_login_styles


def _verify_openai_api_key(key: str) -> tuple[bool, str, bool]:
    """
    Return (accepted, message, verified_live).

    Live verification uses a lightweight models.list() call.
    The key is never included in the returned message.
    """
    if not looks_like_openai_api_key(key):
        return False, "That does not look like an OpenAI API key. Keys usually start with sk-.", False
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key, timeout=20)
        client.models.list()
        return True, "Signed in. Your key is kept in this session only.", True
    except Exception as exc:
        text = str(exc).lower()
        if any(token in text for token in ("invalid", "unauthorized", "401", "incorrect api key", "authentication")):
            return False, "OpenAI rejected this API key. Check it on platform.openai.com.", False
        return (
            True,
            "The key format looks right, but OpenAI could not be reached to confirm it. You can continue; live chat may still fail if the key is invalid.",
            False,
        )


def sign_out() -> None:
    """Clear the runtime key and return the visitor to the login card."""
    st.session_state.clinic_logged_in = False
    st.session_state.openai_api_key_override = ""
    st.session_state.visitor_name = ""
    from src.config import clear_runtime_api_key

    clear_runtime_api_key()
    st.rerun()


def render_login_page() -> None:
    inject_login_styles()

    st.markdown(
        f"""
        <div class="mg-login-stage">
            <div class="mg-login-orb mg-login-orb-a"></div>
            <div class="mg-login-orb mg-login-orb-b"></div>
            <div class="mg-login-orb mg-login-orb-c"></div>
            <div class="mg-login-hero">
                <div class="mg-login-mark-wrap">
                    <div class="mg-login-ring"></div>
                    <div class="mg-login-mark">{LOGO_SVG}</div>
                </div>
                <div class="mg-kicker">Secure session access</div>
                <h1>{APP_NAME}</h1>
                <p>{APP_TAGLINE}</p>
                <svg class="mg-login-ecg" viewBox="0 0 320 36" aria-hidden="true">
                    <path d="M0 20 H48 L58 20 L68 6 L80 32 L92 20 H140 L150 20 L160 8 L172 30 L184 20 H320" />
                </svg>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, card, right = st.columns([0.55, 1.35, 0.55])
    with card:
        with st.form("clinic_login_form", clear_on_submit=False):
            st.markdown("**Enter the clinic**")
            st.caption(
                "Paste your OpenAI API key to start a private educational consultation. "
                "A ChatGPT subscription does not automatically include API credits."
            )
            visitor_name = st.text_input(
                "Your name (optional)",
                placeholder="For example: Ayesha",
                help="This is only used to greet you. It is not a patient account.",
            )
            api_key = st.text_input(
                "OpenAI API key",
                type="password",
                placeholder="sk-...",
                help="Kept in this browser session only. MediGuide does not save it to a file.",
            )
            model_name = st.text_input(
                "Model name",
                value=st.session_state.get("model_name_override") or get_model_name() or DEFAULT_MODEL,
                help="Example: gpt-4o-mini. Your OpenAI account must have access to this model.",
            )
            submitted = st.form_submit_button("Enter clinic", type="primary", width="stretch")

        if submitted:
            key = (api_key or "").strip()
            if not key:
                st.error("Please paste your OpenAI API key to continue.", icon=":material/key:")
            else:
                accepted, message, verified = _verify_openai_api_key(key)
                if not accepted:
                    st.error(message, icon=":material/error:")
                else:
                    st.session_state.openai_api_key_override = key
                    st.session_state.model_name_override = (model_name or DEFAULT_MODEL).strip() or DEFAULT_MODEL
                    st.session_state.visitor_name = (visitor_name or "").strip()
                    st.session_state.clinic_logged_in = True
                    apply_runtime_api_key(key, st.session_state.model_name_override)
                    st.session_state.login_status = message
                    st.session_state.key_verified_live = verified
                    st.rerun()

        st.markdown(
            """
            <div class="mg-login-points">
                <div class="mg-login-point"><strong>Session only.</strong> The key stays in memory for this visit and is not written to disk.</div>
                <div class="mg-login-point"><strong>Not a patient account.</strong> This is an educational prototype, not a hospital login.</div>
                <div class="mg-login-point"><strong>Not a diagnosis.</strong> MediGuide shares general information to discuss with a clinician.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Create or copy a key at platform.openai.com/api-keys. Never share your key in chat, email, or screenshots.")

        st.markdown(
            f'<div class="mg-disclaimer" style="margin-top:1rem;">{MEDICAL_DISCLAIMER}</div>',
            unsafe_allow_html=True,
        )
        st.caption("If this may be an emergency, seek emergency help immediately. Do not wait on this app.")
