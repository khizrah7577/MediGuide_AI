"""
Professional medical chatbot page.

The chat can collect a short patient profile, run emergency checks
before any model call, request a structured assessment, then continue
as a follow-up educational conversation.
"""

from __future__ import annotations

import re
from typing import Any

import streamlit as st

from src.assessment_service import build_explanation_stream, run_assessment, run_safety_only
from src.chains import classify_llm_error, stream_chat_followup
from src.config import (
    ACTIVITY_IMPACT_OPTIONS,
    BLOOD_GROUP_OPTIONS,
    CONTACT_OPTIONS,
    DURATION_OPTIONS,
    GENDER_OPTIONS,
    ONSET_OPTIONS,
    PAGE_RESULTS,
    PREGNANCY_OPTIONS,
    RESPONSE_LANGUAGES,
    SLEEP_OPTIONS,
    SMOKING_OPTIONS,
    TRAVEL_OPTIONS,
    has_api_key,
)
from src.utils import fingerprint_payload
from ui.components import (
    disclaimer_box,
    educational_note,
    emergency_banner,
    render_page_intro,
    render_structured_chat_cards,
)
from ui.styles import inject_form_styles

WELCOME_MESSAGE = (
    "Hello. I am MediGuide, an educational clinic assistant. "
    "Tell me how you feel in your own words. I can help you organise symptoms "
    "and share general information to discuss with a qualified healthcare professional. "
    "I do not diagnose illness, and I am not emergency care.\n\n"
    "If this may be an emergency, seek emergency help immediately."
)

SUGGESTIONS = {
    ":blue[:material/air:] Runny nose and sore throat": (
        "I have a runny nose and a sore throat for about two days. Severity feels like 2 out of 10."
    ),
    ":orange[:material/coronavirus:] Fever and cough": (
        "I have had a fever and cough for 4 to 7 days. Severity feels like 6 out of 10."
    ),
    ":red[:material/emergency:] Chest pain and breathing trouble": (
        "I have severe chest pain and shortness of breath."
    ),
}

ASSISTANT_AVATAR = ":material/stethoscope:"
USER_AVATAR = ":material/person:"


def _option_index(options: tuple[str, ...] | list[str], current: str | None) -> int:
    values = list(options)
    if current in values:
        return values.index(current)
    return 0


def _default_profile() -> dict[str, Any]:
    return {
        "name": st.session_state.get("form_name", ""),
        "age": st.session_state.get("form_age", ""),
        "gender": st.session_state.get("form_gender", GENDER_OPTIONS[0]),
        "city": st.session_state.get("form_city", ""),
        "blood_group": st.session_state.get("form_blood_group", BLOOD_GROUP_OPTIONS[0]),
        "pregnancy": st.session_state.get("form_pregnancy", PREGNANCY_OPTIONS[0]),
        "height": st.session_state.get("form_height", ""),
        "weight": st.session_state.get("form_weight", ""),
        "duration": st.session_state.get("form_duration", DURATION_OPTIONS[0]),
        "onset": st.session_state.get("form_onset", ONSET_OPTIONS[0]),
        "severity": int(st.session_state.get("form_severity", 3)),
        "temperature": st.session_state.get("form_temperature", ""),
        "pain_location": st.session_state.get("form_pain_location", ""),
        "activity": st.session_state.get("form_activity", ACTIVITY_IMPACT_OPTIONS[0]),
        "sleep": st.session_state.get("form_sleep", SLEEP_OPTIONS[0]),
        "smoking": st.session_state.get("form_smoking", SMOKING_OPTIONS[0]),
        "travel": st.session_state.get("form_travel", TRAVEL_OPTIONS[0]),
        "contact": st.session_state.get("form_contact", CONTACT_OPTIONS[0]),
        "allergies": st.session_state.get("form_allergies", ""),
        "language": st.session_state.get("default_language", "English"),
        "conditions": st.session_state.get("form_conditions", ""),
        "medications": st.session_state.get("form_medications", ""),
        "notes": st.session_state.get("form_notes", ""),
    }


def _ensure_profile() -> dict[str, Any]:
    merged = _default_profile()
    current = st.session_state.get("chat_profile") or {}
    merged.update({key: value for key, value in current.items() if value is not None})
    return merged


def _profile_extra_details(profile: dict[str, Any]) -> dict[str, str]:
    return {
        "Preferred name": str(profile.get("name") or ""),
        "City or area": str(profile.get("city") or ""),
        "Blood group": str(profile.get("blood_group") or ""),
        "Pregnancy status": str(profile.get("pregnancy") or ""),
        "Height in cm": str(profile.get("height") or ""),
        "Weight in kg": str(profile.get("weight") or ""),
        "Symptom onset": str(profile.get("onset") or ""),
        "Measured temperature": str(profile.get("temperature") or ""),
        "Pain location": str(profile.get("pain_location") or ""),
        "Activity impact": str(profile.get("activity") or ""),
        "Sleep last night": str(profile.get("sleep") or ""),
        "Smoking or vaping": str(profile.get("smoking") or ""),
        "Recent travel": str(profile.get("travel") or ""),
        "Contact with someone unwell": str(profile.get("contact") or ""),
        "Known allergies": str(profile.get("allergies") or ""),
    }


def _extract_age(text: str) -> str | None:
    """Accept a plain age, or a short 'I am 25' sentence. Avoid treating '2 days' as age."""
    cleaned = (text or "").strip()
    if re.fullmatch(r"\d{1,3}", cleaned):
        value = int(cleaned)
        return cleaned if 0 <= value <= 120 else None
    match = re.search(r"\b(?:i am|i'm|age(?:\s+is)?)\s+(\d{1,3})\b", cleaned, flags=re.I)
    if match:
        value = int(match.group(1))
        return str(value) if 0 <= value <= 120 else None
    return None


def _recent_conversation(messages: list[dict[str, Any]], limit: int = 8) -> str:
    lines = []
    for item in messages[-limit:]:
        role = "User" if item.get("role") == "user" else "Assistant"
        content = str(item.get("content") or "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _render_message(message: dict[str, Any]) -> None:
    avatar = ASSISTANT_AVATAR if message.get("role") == "assistant" else USER_AVATAR
    with st.chat_message(message.get("role", "assistant"), avatar=avatar):
        if message.get("emergency"):
            st.error(message["content"], icon=":material/emergency:")
        else:
            st.markdown(message.get("content") or "")
        if message.get("structured"):
            render_structured_chat_cards(message["structured"])


def _run_chat_assessment(user_text: str, profile: dict[str, Any]) -> dict[str, Any]:
    form_data = {
        "age": profile.get("age", ""),
        "gender": profile.get("gender", GENDER_OPTIONS[0]),
        "symptoms": [],
        "free_text_symptoms": user_text,
        "duration": profile.get("duration", DURATION_OPTIONS[-1]),
        "severity": int(profile.get("severity", 3)),
        "medical_conditions": profile.get("conditions", ""),
        "medications": profile.get("medications", ""),
        "additional_notes": profile.get("notes", ""),
        "response_language": profile.get("language", "English"),
        "extra_details": _profile_extra_details(profile),
    }
    outcome = run_assessment(
        form_data,
        save_history=bool(st.session_state.get("history_enabled")),
    )
    return outcome.to_session_dict()


def _persist_profile(profile: dict[str, Any]) -> None:
    st.session_state.chat_profile = profile
    st.session_state.form_name = profile.get("name", "")
    st.session_state.form_age = profile.get("age", "")
    st.session_state.form_gender = profile.get("gender")
    st.session_state.form_city = profile.get("city", "")
    st.session_state.form_blood_group = profile.get("blood_group")
    st.session_state.form_pregnancy = profile.get("pregnancy")
    st.session_state.form_height = profile.get("height", "")
    st.session_state.form_weight = profile.get("weight", "")
    st.session_state.form_duration = profile.get("duration")
    st.session_state.form_onset = profile.get("onset")
    st.session_state.form_severity = profile.get("severity")
    st.session_state.form_temperature = profile.get("temperature", "")
    st.session_state.form_pain_location = profile.get("pain_location", "")
    st.session_state.form_activity = profile.get("activity")
    st.session_state.form_sleep = profile.get("sleep")
    st.session_state.form_smoking = profile.get("smoking")
    st.session_state.form_travel = profile.get("travel")
    st.session_state.form_contact = profile.get("contact")
    st.session_state.form_allergies = profile.get("allergies", "")
    st.session_state.form_conditions = profile.get("conditions", "")
    st.session_state.form_medications = profile.get("medications", "")
    st.session_state.form_notes = profile.get("notes", "")
    st.session_state.form_language = profile.get("language")
    st.session_state.default_language = profile.get("language")


def render_chat_page() -> None:
    inject_form_styles()
    render_page_intro(
        "Medical chat",
        "A professional educational consultation chat. Not a diagnosis and not emergency care.",
    )
    disclaimer_box()

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": WELCOME_MESSAGE, "kind": "welcome"}
        ]
    profile = _ensure_profile()
    key_ready = has_api_key() or bool(st.session_state.get("openai_api_key_override"))
    if not key_ready:
        st.warning(
            "No OpenAI API key is configured. You can still chat locally for emergency "
            "keyword checks. Live educational replies need an API key in Settings.",
            icon=":material/key:",
        )

    with st.expander("Patient profile for this chat", expanded=not bool(str(profile.get("age") or "").strip())):
        st.markdown(
            """
            <div class="mg-form-banner">
                <div class="mg-form-orb"></div>
                <h3>Tell MediGuide more about this visit</h3>
                <p>Age is required for a full educational assessment. Extra details stay optional and are not written to history.</p>
                <div class="mg-form-steps">
                    <span class="mg-form-step">1 About you</span>
                    <span class="mg-form-step">2 Symptoms</span>
                    <span class="mg-form-step">3 Daily context</span>
                    <span class="mg-form-step">4 Background</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="mg-form-section"><span class="mg-form-section-num">01</span><h4>About you</h4></div>',
            unsafe_allow_html=True,
        )
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            profile["name"] = st.text_input("Preferred name", value=str(profile.get("name") or ""), placeholder="Optional")
            profile["age"] = st.text_input("Age", value=str(profile.get("age") or ""), help="Needed before a full educational assessment.")
        with col_b:
            profile["gender"] = st.selectbox(
                "Gender",
                list(GENDER_OPTIONS),
                index=_option_index(GENDER_OPTIONS, profile.get("gender")),
            )
            profile["city"] = st.text_input("City or area", value=str(profile.get("city") or ""), placeholder="Optional")
        with col_c:
            profile["language"] = st.selectbox(
                "Reply language",
                list(RESPONSE_LANGUAGES),
                index=_option_index(RESPONSE_LANGUAGES, profile.get("language")),
            )
            profile["blood_group"] = st.selectbox(
                "Blood group",
                list(BLOOD_GROUP_OPTIONS),
                index=_option_index(BLOOD_GROUP_OPTIONS, profile.get("blood_group")),
            )
        col_h, col_w, col_p = st.columns(3)
        with col_h:
            profile["height"] = st.text_input("Height in cm", value=str(profile.get("height") or ""), placeholder="Optional")
        with col_w:
            profile["weight"] = st.text_input("Weight in kg", value=str(profile.get("weight") or ""), placeholder="Optional")
        with col_p:
            profile["pregnancy"] = st.selectbox(
                "Pregnancy status",
                list(PREGNANCY_OPTIONS),
                index=_option_index(PREGNANCY_OPTIONS, profile.get("pregnancy")),
            )

        st.markdown(
            '<div class="mg-form-section"><span class="mg-form-section-num">02</span><h4>Symptoms</h4></div>',
            unsafe_allow_html=True,
        )
        col_d, col_e, col_f = st.columns(3)
        with col_d:
            profile["duration"] = st.selectbox(
                "Symptom duration",
                list(DURATION_OPTIONS),
                index=_option_index(DURATION_OPTIONS, profile.get("duration")),
            )
        with col_e:
            profile["onset"] = st.selectbox(
                "How did this start?",
                list(ONSET_OPTIONS),
                index=_option_index(ONSET_OPTIONS, profile.get("onset")),
            )
        with col_f:
            profile["severity"] = st.slider(
                "How severe does this feel to you?",
                min_value=1,
                max_value=10,
                value=int(profile.get("severity", 3)),
                help="Your own rating, not a clinical score.",
            )
        col_t, col_pain = st.columns(2)
        with col_t:
            profile["temperature"] = st.text_input(
                "Temperature if measured",
                value=str(profile.get("temperature") or ""),
                placeholder="Optional, for example 38.2 C",
            )
        with col_pain:
            profile["pain_location"] = st.text_input(
                "If there is pain, where is it?",
                value=str(profile.get("pain_location") or ""),
                placeholder="Optional",
            )
        profile["activity"] = st.selectbox(
            "How much are usual activities affected?",
            list(ACTIVITY_IMPACT_OPTIONS),
            index=_option_index(ACTIVITY_IMPACT_OPTIONS, profile.get("activity")),
        )

        st.markdown(
            '<div class="mg-form-section"><span class="mg-form-section-num">03</span><h4>Daily context</h4></div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            profile["sleep"] = st.selectbox(
                "Sleep last night",
                list(SLEEP_OPTIONS),
                index=_option_index(SLEEP_OPTIONS, profile.get("sleep")),
            )
        with c2:
            profile["smoking"] = st.selectbox(
                "Smoking or vaping",
                list(SMOKING_OPTIONS),
                index=_option_index(SMOKING_OPTIONS, profile.get("smoking")),
            )
        with c3:
            profile["travel"] = st.selectbox(
                "Recent travel",
                list(TRAVEL_OPTIONS),
                index=_option_index(TRAVEL_OPTIONS, profile.get("travel")),
            )
        profile["contact"] = st.selectbox(
            "Contact with someone who was unwell",
            list(CONTACT_OPTIONS),
            index=_option_index(CONTACT_OPTIONS, profile.get("contact")),
        )

        st.markdown(
            '<div class="mg-form-section"><span class="mg-form-section-num">04</span><h4>Background</h4></div>',
            unsafe_allow_html=True,
        )
        profile["conditions"] = st.text_input(
            "Existing conditions (optional)",
            value=str(profile.get("conditions") or ""),
        )
        profile["allergies"] = st.text_input(
            "Known allergies (optional)",
            value=str(profile.get("allergies") or ""),
        )
        profile["medications"] = st.text_input(
            "Current medications (optional)",
            value=str(profile.get("medications") or ""),
            help="Optional. Medications are not stored in history.",
        )
        profile["notes"] = st.text_area(
            "Additional notes (optional)",
            value=str(profile.get("notes") or ""),
            placeholder="Anything else you want the educational reply to consider",
        )
        _persist_profile(profile)

    toolbar = st.container(horizontal=True)
    with toolbar:
        if st.button("New chat", icon=":material/chat_add_on:"):
            st.session_state.chat_messages = [
                {"role": "assistant", "content": WELCOME_MESSAGE, "kind": "welcome"}
            ]
            st.session_state.chat_assessment_done = False
            st.rerun()
        if st.session_state.get("last_outcome"):
            if st.button("Open results desk", icon=":material/clinical_notes:"):
                st.session_state.current_page = PAGE_RESULTS
                st.rerun()

    chat_box = st.container()
    with chat_box:
        for message in st.session_state.chat_messages:
            _render_message(message)

    prompt = st.bottom.chat_input(
        "Describe your symptoms or ask a follow-up question...",
        submit_mode="disable",
    )

    user_messages = [item for item in st.session_state.chat_messages if item.get("role") == "user"]
    if not user_messages:
        suggestions = st.empty()
        selected = suggestions.pills(
            "Try a sample message",
            list(SUGGESTIONS.keys()),
            label_visibility="collapsed",
        )
        if selected:
            prompt = SUGGESTIONS[selected]
        if prompt:
            suggestions.empty()

    if not prompt:
        educational_note()
        return

    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    possible_age = _extract_age(prompt)
    if possible_age and not str(profile.get("age") or "").strip():
        profile["age"] = possible_age
        _persist_profile(profile)

    extra_text = " ".join(
        str(value) for value in _profile_extra_details(profile).values() if str(value).strip()
    )
    safety = run_safety_only(
        symptoms=[],
        free_text_symptoms=prompt,
        additional_notes=f"{profile.get('notes', '')} {extra_text}".strip(),
    )
    if safety.possible_emergency:
        extra = safety.urdu_warning_message if profile.get("language") == "Urdu" else ""
        emergency_banner(safety.warning_message, extra)
        st.session_state.emergency_alert = safety.warning_message

    greeting_only = prompt.strip().lower().rstrip(".!") in {
        "hi",
        "hello",
        "hey",
        "salam",
        "assalam",
        "thanks",
        "thank you",
        "ok",
        "okay",
    }

    if not str(profile.get("age") or "").strip():
        reply = (
            "I can keep chatting, but I need your age before a full educational "
            "assessment. Type your age, or enter it in the patient profile above."
        )
        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            st.markdown(reply)
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        return

    if greeting_only and not st.session_state.get("chat_assessment_done"):
        reply = (
            "Hello. Please tell me the symptoms you want to organise — for example "
            "fever, cough, headache — and how long they have lasted."
        )
        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            st.markdown(reply)
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        return

    fingerprint = fingerprint_payload(
        {
            "age": profile.get("age"),
            "text": prompt,
            "duration": profile.get("duration"),
            "severity": profile.get("severity"),
            "language": profile.get("language"),
            "extra": _profile_extra_details(profile),
        }
    )
    already_assessed = bool(st.session_state.get("chat_assessment_done"))
    run_full_assessment = safety.possible_emergency or not already_assessed

    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        try:
            if run_full_assessment:
                with st.status(":shimmer[Reviewing your symptoms]", type="compact") as status:
                    if safety.possible_emergency:
                        st.write("Emergency keyword check ran before any AI request.")
                    outcome = _run_chat_assessment(prompt, profile)
                    st.session_state.last_outcome = outcome
                    st.session_state.last_submission_hash = fingerprint
                    st.session_state.chat_assessment_done = bool(outcome.get("structured"))
                    status.update(label="Educational review ready", state="complete")

                if outcome.get("error") and not outcome.get("structured"):
                    st.error(outcome["error"], icon=":material/error:")
                    assistant_text = outcome["error"]
                    st.session_state.chat_messages.append(
                        {"role": "assistant", "content": assistant_text}
                    )
                else:
                    structured = outcome.get("structured") or {}
                    if outcome.get("safety", {}).get("possible_emergency"):
                        st.error(
                            outcome["safety"].get("warning_message") or "Possible emergency warning.",
                            icon=":material/emergency:",
                        )
                    can_stream = bool(outcome.get("model_called")) and bool(structured) and key_ready
                    if can_stream:
                        st.caption(
                            "This streamed explanation is a second model call, "
                            "separate from the JSON assessment."
                        )
                        try:
                            generator = build_explanation_stream(outcome.get("patient") or {}, structured)
                            assistant_text = st.write_stream(generator)
                        except Exception as exc:
                            assistant_text = classify_llm_error(exc)
                            st.warning(assistant_text)
                    else:
                        assistant_text = structured.get("summary") or outcome.get("error") or (
                            "I have organised your details. Live AI text is unavailable without an API key."
                        )
                        st.write(assistant_text)
                    render_structured_chat_cards(structured)
                    st.session_state.streamed_explanation = assistant_text
                    st.session_state.chat_messages.append(
                        {
                            "role": "assistant",
                            "content": assistant_text,
                            "structured": structured,
                            "emergency": bool(outcome.get("safety", {}).get("possible_emergency")),
                        }
                    )
            else:
                last_outcome = st.session_state.get("last_outcome") or {}
                structured = last_outcome.get("structured") or {}
                prior = structured.get("summary") or "No previous educational summary is stored."
                conversation = _recent_conversation(st.session_state.chat_messages)
                with st.status(":shimmer[Thinking]", type="compact") as status:
                    status.update(label="Reply ready", state="complete")
                st.caption("This follow-up is a separate model call from the original assessment.")
                try:
                    assistant_text = st.write_stream(
                        stream_chat_followup(
                            user_message=prompt,
                            conversation=conversation,
                            prior_summary=prior,
                            response_language=str(profile.get("language") or "English"),
                        )
                    )
                except Exception as exc:
                    assistant_text = classify_llm_error(exc)
                    st.warning(assistant_text)
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": assistant_text}
                )
        except Exception as exc:
            friendly = classify_llm_error(exc)
            st.error(friendly, icon=":material/error:")
            st.session_state.chat_messages.append({"role": "assistant", "content": friendly})
