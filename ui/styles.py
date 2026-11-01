"""
Medical clinic theme extras for MediGuide AI.

Most colours, fonts, and radii live in .streamlit/config.toml.
This CSS only adds clinic-specific cards, chat polish, and
emergency/disclaimer emphasis. It does not hide the sidebar,
navigation, or page content.
"""

from __future__ import annotations

import streamlit as st

MEDICAL_CSS = """
<style>
    html, body, .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp span {
        font-variant-ligatures: none;
        font-feature-settings: "liga" 0, "clig" 0;
    }

    .stApp {
        background:
            radial-gradient(1200px 420px at 8% -10%, rgba(45, 212, 191, 0.16), transparent 55%),
            radial-gradient(900px 380px at 100% 0%, rgba(14, 116, 144, 0.10), transparent 50%),
            linear-gradient(180deg, #E7F4F1 0%, #F3F8F7 180px, #F3F8F7 100%);
    }

    .block-container {
        max-width: 1120px;
    }

    .mg-hero {
        background: linear-gradient(135deg, #07343A 0%, #0F766E 58%, #0E7490 100%);
        color: #FFFFFF;
        border-radius: 22px;
        padding: 1.55rem 1.7rem 1.45rem 1.7rem;
        box-shadow: 0 16px 40px rgba(7, 52, 58, 0.22);
        margin-bottom: 1rem;
        border: 1px solid rgba(94, 234, 212, 0.22);
    }

    .mg-kicker {
        font-size: 0.74rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #99F6E4;
        margin-bottom: 0.3rem;
        font-weight: 650;
    }

    .mg-hero h1 {
        color: #FFFFFF !important;
        font-size: 2rem;
        margin: 0 0 0.3rem 0;
    }

    .mg-hero p {
        margin: 0;
        color: #CCFBF1;
        font-size: 1.05rem;
    }

    .mg-logo-row {
        display: flex;
        gap: 1rem;
        align-items: center;
    }

    .mg-mark {
        width: 58px;
        height: 58px;
        min-width: 58px;
        border-radius: 18px;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.22);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .mg-card {
        background: #FFFFFF;
        border: 1px solid #C5DDD8;
        border-radius: 16px;
        padding: 1.1rem 1.15rem;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        margin-bottom: 0.85rem;
    }

    .mg-step {
        background: #FFFFFF;
        border: 1px solid #C5DDD8;
        border-radius: 16px;
        padding: 1rem;
        height: 100%;
    }

    .mg-step-number {
        width: 32px;
        height: 32px;
        border-radius: 999px;
        background: #CCFBF1;
        color: #115E59;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0.5rem;
    }

    .mg-disclaimer {
        background: #FFF7ED;
        border: 1px solid #FDBA74;
        border-left: 6px solid #EA580C;
        border-radius: 14px;
        padding: 0.9rem 1rem;
        color: #7C2D12;
        margin: 0.55rem 0 0.9rem 0;
        line-height: 1.45;
        font-size: 0.92rem;
    }

    .mg-emergency {
        background: #FEF3F2;
        border: 1px solid #FECDCA;
        border-left: 6px solid #B42318;
        border-radius: 14px;
        padding: 1rem 1.05rem;
        color: #7A271A;
        margin-bottom: 1rem;
    }

    .mg-emergency h3 {
        color: #7A271A !important;
        margin: 0 0 0.4rem 0;
    }

    .mg-pill {
        display: inline-block;
        border-radius: 999px;
        padding: 0.22rem 0.72rem;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.03em;
    }

    .mg-pill-low { background: #ECFDF3; color: #166534; border: 1px solid #A7F3D0; }
    .mg-pill-medium { background: #FFFAEB; color: #92400E; border: 1px solid #FCD34D; }
    .mg-pill-high { background: #FEF6EE; color: #9A3412; border: 1px solid #FDBA74; }
    .mg-pill-emergency { background: #FEF3F2; color: #991B1B; border: 1px solid #FCA5A5; }

    .mg-muted { color: #4B6A72; font-size: 0.92rem; }

    .mg-clinic-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin: 0.35rem 0 0.85rem 0;
    }

    .mg-chip {
        background: #FFFFFF;
        border: 1px solid #C5DDD8;
        color: #115E59;
        border-radius: 999px;
        padding: 0.22rem 0.7rem;
        font-size: 0.8rem;
        font-weight: 600;
    }

    [data-testid="stChatMessage"] {
        background: rgba(255,255,255,0.72);
        border: 1px solid #D7E8E4;
        border-radius: 16px;
        padding: 0.15rem 0.35rem;
        margin-bottom: 0.55rem;
    }

    [data-testid="stBottom"] {
        background: linear-gradient(180deg, rgba(243,248,247,0.2), #F3F8F7 35%);
        border-top: 1px solid #C5DDD8;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #07343A 0%, #0A3F46 100%);
    }

    header[data-testid="stHeader"] {
        background: rgba(243, 248, 247, 0.86);
    }

    @media (max-width: 768px) {
        .mg-hero { padding: 1.15rem 1.1rem; }
        .mg-hero h1 { font-size: 1.42rem; }
    }
</style>
"""

LOGO_SVG = """
<svg width="34" height="34" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <rect width="48" height="48" rx="14" fill="#0F766E"/>
  <circle cx="24" cy="24" r="15" fill="#ECFDF5"/>
  <path d="M21.5 12h5v10h10v5h-10v10h-5V27h-10v-5h10V12z" fill="#0F766E"/>
</svg>
"""


LOGIN_CSS = """
<style>
    section[data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    html, body, .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label {
        font-variant-ligatures: none;
        font-feature-settings: "liga" 0, "clig" 0;
    }

    @keyframes mgLoginFadeUp {
        from { opacity: 0; transform: translateY(22px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes mgLoginFloat {
        0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
        50% { transform: translate3d(0, -14px, 0) scale(1.06); }
    }
    @keyframes mgLoginDrift {
        0%, 100% { transform: translate3d(0, 0, 0); }
        50% { transform: translate3d(18px, 12px, 0); }
    }
    @keyframes mgLoginShimmer {
        0% { background-position: 0% 40%; }
        100% { background-position: 100% 60%; }
    }
    @keyframes mgLoginPulse {
        0%, 100% { transform: scale(1); opacity: 0.45; }
        50% { transform: scale(1.28); opacity: 0; }
    }
    @keyframes mgLoginGlow {
        0%, 100% { box-shadow: 0 12px 30px rgba(7, 52, 58, 0.25); }
        50% { box-shadow: 0 16px 36px rgba(45, 212, 191, 0.38); }
    }
    @keyframes mgLoginButton {
        0%, 100% { box-shadow: 0 8px 18px rgba(15, 118, 110, 0.22); }
        50% { box-shadow: 0 14px 30px rgba(15, 118, 110, 0.42); }
    }
    @keyframes mgLoginDash {
        to { stroke-dashoffset: -240; }
    }

    .stApp {
        background:
            radial-gradient(900px 420px at 8% -8%, rgba(45, 212, 191, 0.30), transparent 55%),
            radial-gradient(800px 380px at 110% 8%, rgba(14, 116, 144, 0.24), transparent 50%),
            linear-gradient(120deg, #07343A, #0F766E, #0E7490, #07343A);
        background-size: auto, auto, 240% 240%;
        animation: mgLoginShimmer 14s linear infinite;
    }

    .block-container {
        padding-top: 2.2rem;
        max-width: 980px;
    }

    .mg-login-stage {
        position: relative;
        overflow: hidden;
        animation: mgLoginFadeUp 0.7s ease both;
        margin-bottom: 0.4rem;
    }

    .mg-login-orb {
        position: absolute;
        border-radius: 50%;
        pointer-events: none;
        filter: blur(0.5px);
    }
    .mg-login-orb-a {
        width: 120px;
        height: 120px;
        right: 8%;
        top: -28px;
        background: rgba(153, 246, 228, 0.22);
        animation: mgLoginFloat 5.5s ease-in-out infinite;
    }
    .mg-login-orb-b {
        width: 74px;
        height: 74px;
        left: 12%;
        top: 18px;
        background: rgba(14, 116, 144, 0.28);
        animation: mgLoginDrift 7s ease-in-out infinite;
    }
    .mg-login-orb-c {
        width: 42px;
        height: 42px;
        right: 24%;
        bottom: 8px;
        background: rgba(255, 255, 255, 0.16);
        animation: mgLoginFloat 4.2s ease-in-out infinite 0.6s;
    }

    .mg-login-hero {
        color: #ECFDF5;
        text-align: center;
        margin-bottom: 1.1rem;
        position: relative;
        z-index: 1;
    }

    .mg-kicker {
        font-size: 0.74rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #99F6E4;
        margin-bottom: 0.3rem;
        font-weight: 650;
    }

    .mg-login-hero h1 {
        color: #FFFFFF !important;
        font-size: 2.35rem;
        margin: 0.35rem 0 0.25rem 0;
        letter-spacing: 0.01em;
    }

    .mg-login-hero p {
        margin: 0 auto;
        max-width: 36rem;
        color: #CCFBF1;
        font-size: 1.08rem;
    }

    .mg-login-mark-wrap {
        width: 92px;
        height: 92px;
        margin: 0 auto 0.85rem auto;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .mg-login-ring {
        position: absolute;
        inset: 0;
        border-radius: 28px;
        border: 2px solid rgba(153, 246, 228, 0.45);
        animation: mgLoginPulse 2.4s ease-out infinite;
    }

    .mg-login-mark {
        width: 72px;
        height: 72px;
        border-radius: 22px;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.24);
        display: flex;
        align-items: center;
        justify-content: center;
        animation: mgLoginGlow 3.2s ease-in-out infinite;
    }

    .mg-login-ecg {
        width: min(320px, 80%);
        height: 36px;
        margin: 0.85rem auto 0 auto;
        display: block;
    }
    .mg-login-ecg path {
        fill: none;
        stroke: #99F6E4;
        stroke-width: 2.4;
        stroke-linecap: round;
        stroke-dasharray: 80 160;
        animation: mgLoginDash 2.8s linear infinite;
    }

    div[data-testid="stForm"] {
        background: rgba(255,255,255,0.94);
        border: 1px solid #C5DDD8;
        border-radius: 22px;
        padding: 1.1rem 1.15rem 0.95rem 1.15rem;
        box-shadow: 0 22px 50px rgba(7, 52, 58, 0.16);
        animation: mgLoginFadeUp 0.8s ease both;
        backdrop-filter: blur(8px);
    }

    div[data-testid="stForm"] .stButton button[kind="primary"] {
        animation: mgLoginButton 2.2s ease-in-out infinite;
        border-radius: 14px;
        font-weight: 700;
    }

    .mg-login-points {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0.55rem;
        margin: 0.8rem 0 0.2rem 0;
    }

    .mg-login-point {
        background: rgba(243, 248, 247, 0.92);
        border: 1px solid #D7E8E4;
        border-radius: 14px;
        padding: 0.7rem 0.85rem;
        color: #12303A;
        font-size: 0.92rem;
        animation: mgLoginFadeUp 0.7s ease both;
    }
    .mg-login-point:nth-child(1) { animation-delay: 0.08s; }
    .mg-login-point:nth-child(2) { animation-delay: 0.16s; }
    .mg-login-point:nth-child(3) { animation-delay: 0.24s; }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    @media (max-width: 768px) {
        .mg-login-hero h1 { font-size: 1.7rem; }
        .mg-login-orb { display: none; }
        .stApp {
            background: linear-gradient(180deg, #07343A 0%, #0F766E 28%, #F3F8F7 28.1%);
            animation: none;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .stApp, .mg-login-orb, .mg-login-ring, .mg-login-mark,
        .mg-login-ecg path, div[data-testid="stForm"],
        .mg-login-point, div[data-testid="stForm"] .stButton button[kind="primary"] {
            animation: none !important;
        }
    }
</style>
"""


def inject_styles() -> None:
    """Apply clinic CSS extras once per rerun."""
    st.markdown(MEDICAL_CSS, unsafe_allow_html=True)


FORM_CSS = """
<style>
    @keyframes mgFadeUp {
        from { opacity: 0; transform: translateY(18px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes mgFloat {
        0%, 100% { transform: translateY(0) scale(1); }
        50% { transform: translateY(-8px) scale(1.03); }
    }
    @keyframes mgShimmer {
        0% { background-position: 0% 50%; }
        100% { background-position: 100% 50%; }
    }
    @keyframes mgPulse {
        0%, 100% { box-shadow: 0 8px 20px rgba(15, 118, 110, 0.18); }
        50% { box-shadow: 0 12px 28px rgba(15, 118, 110, 0.35); }
    }
    @keyframes mgGlow {
        0%, 100% { opacity: 0.45; }
        50% { opacity: 0.9; }
    }

    .mg-form-banner {
        position: relative;
        overflow: hidden;
        background: linear-gradient(120deg, #07343A, #0F766E, #0E7490, #0F766E);
        background-size: 220% 220%;
        animation: mgFadeUp 0.55s ease both, mgShimmer 8s linear infinite;
        color: #ECFDF5;
        border-radius: 22px;
        padding: 1.25rem 1.35rem 1.15rem 1.35rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(153, 246, 228, 0.28);
        box-shadow: 0 18px 36px rgba(7, 52, 58, 0.18);
    }
    .mg-form-banner h3 {
        color: #FFFFFF !important;
        margin: 0 0 0.35rem 0;
    }
    .mg-form-banner p {
        margin: 0 0 0.8rem 0;
        color: #CCFBF1;
    }
    .mg-form-orb {
        position: absolute;
        width: 88px;
        height: 88px;
        right: 18px;
        top: -18px;
        border-radius: 50%;
        background: rgba(153, 246, 228, 0.22);
        animation: mgFloat 4.5s ease-in-out infinite, mgGlow 3.6s ease-in-out infinite;
        pointer-events: none;
    }
    .mg-form-orb-2 {
        left: 10%;
        right: auto;
        top: auto;
        bottom: -26px;
        width: 62px;
        height: 62px;
        background: rgba(14, 116, 144, 0.28);
        animation-delay: 1.1s;
    }
    .mg-form-steps {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
    }
    .mg-form-step {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.22);
        color: #ECFDF5;
        border-radius: 999px;
        padding: 0.28rem 0.7rem;
        font-size: 0.8rem;
        font-weight: 650;
        animation: mgFadeUp 0.7s ease both;
    }
    .mg-form-step:nth-child(2) { animation-delay: 0.08s; }
    .mg-form-step:nth-child(3) { animation-delay: 0.16s; }
    .mg-form-step:nth-child(4) { animation-delay: 0.24s; }

    .mg-form-section {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        animation: mgFadeUp 0.55s ease both;
        margin: 1rem 0 0.2rem 0;
        padding-top: 0.35rem;
        border-top: 1px solid rgba(197, 221, 216, 0.8);
    }
    .mg-form-section-num {
        min-width: 38px;
        height: 38px;
        border-radius: 12px;
        background: linear-gradient(135deg, #0F766E, #0E7490);
        color: #ECFDF5;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 750;
        font-size: 0.82rem;
        letter-spacing: 0.04em;
        box-shadow: 0 8px 16px rgba(15, 118, 110, 0.22);
    }
    .mg-form-section h4 {
        margin: 0;
        color: #07343A !important;
        font-size: 1.12rem;
    }

    div[data-testid="stForm"] {
        background: rgba(255,255,255,0.88);
        border: 1px solid #C5DDD8;
        border-radius: 22px;
        padding: 1rem 1.05rem 0.85rem 1.05rem;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
        animation: mgFadeUp 0.65s ease both;
        backdrop-filter: blur(6px);
    }

    div[data-testid="stForm"] .stButton button[kind="primary"] {
        animation: mgPulse 2.4s ease-in-out infinite;
        border-radius: 14px;
        font-weight: 700;
    }

    @media (max-width: 768px) {
        .mg-form-orb { display: none; }
        .mg-form-banner { padding: 1rem; }
    }
</style>
"""


def inject_login_styles() -> None:
    """Login-only layout: hide clinic navigation and centre the sign-in card."""
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)


def inject_form_styles() -> None:
    """Animated clinic-intake styles used only on the symptom form."""
    st.markdown(FORM_CSS, unsafe_allow_html=True)
