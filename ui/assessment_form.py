"""
Patient symptom assessment form.

Validation and emergency checks run before any model request.
"""

from __future__ import annotations

import streamlit as st

from src.assessment_service import run_assessment, run_safety_only
from src.config import (
    ACTIVITY_IMPACT_OPTIONS,
    BLOOD_GROUP_OPTIONS,
    COMMON_SYMPTOMS,
    CONTACT_OPTIONS,
    DURATION_OPTIONS,
    GENDER_OPTIONS,
    ONSET_OPTIONS,
    PAGE_CHAT,
    PAGE_RESULTS,
    PREGNANCY_OPTIONS,
    RESPONSE_LANGUAGES,
    SLEEP_OPTIONS,
    SMOKING_OPTIONS,
    TRAVEL_OPTIONS,
    has_api_key,
)
from src.utils import fingerprint_payload
from src.validation import validate_patient_input
from ui.components import disclaimer_box, educational_note, emergency_banner, render_page_intro
from ui.styles import inject_form_styles


def _option_index(options: tuple[str, ...] | list[str], current: str | None) -> int:
    values = list(options)
    if current in values:
        return values.index(current)
    return 0


def _section(step: str, title: str, caption: str) -> None:
    st.markdown(
        f"""
        <div class="mg-form-section">
            <span class="mg-form-section-num">{step}</span>
            <h4>{title}</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(caption)


def render_assessment_form() -> None:
    inject_form_styles()
    render_page_intro(
        "Symptom form",
        "A guided clinic intake. Required fields are age, symptoms, duration, and perceived severity.",
        icon=":material/assignment:",
    )
    st.markdown(
        """
        <div class="mg-form-banner">
            <div class="mg-form-orb"></div>
            <div class="mg-form-orb mg-form-orb-2"></div>
            <h3>Tell MediGuide more about this visit</h3>
            <p>The extra details stay educational. They help organise your story for a clinician. They do not confirm a diagnosis.</p>
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
    disclaimer_box()

    if st.button("Prefer to chat instead?", icon=":material/stethoscope:"):
        st.session_state.current_page = PAGE_CHAT
        st.rerun()

    if not has_api_key() and not st.session_state.get("openai_api_key_override"):
        st.warning(
            "No OpenAI API key is configured. You can still fill the form. "
            "Emergency keyword checks will run, but live AI text will not be generated.",
            icon=":material/key:",
        )

    force_new = st.checkbox(
        "Force a new model request even if the details look unchanged",
        value=False,
        help="Use this if you want to send the same form again on purpose.",
    )

    with st.form("assessment_form", clear_on_submit=False):
        _section("01", "About you", "Required: age. Everything else in this block is optional.")
        c1, c2, c3 = st.columns(3)
        with c1:
            preferred_name = st.text_input(
                "Preferred name",
                value=st.session_state.get("form_name", ""),
                placeholder="Optional",
            )
            age = st.text_input(
                "Age",
                value=st.session_state.get("form_age", ""),
                help="Enter a whole number. Age is used as context, not to confirm a diagnosis.",
            )
        with c2:
            gender = st.selectbox(
                "Gender",
                options=list(GENDER_OPTIONS),
                index=_option_index(GENDER_OPTIONS, st.session_state.get("form_gender")),
                help="The app never infers gender.",
            )
            city = st.text_input(
                "City or area",
                value=st.session_state.get("form_city", ""),
                placeholder="Optional",
            )
        with c3:
            blood_group = st.selectbox(
                "Blood group",
                options=list(BLOOD_GROUP_OPTIONS),
                index=_option_index(BLOOD_GROUP_OPTIONS, st.session_state.get("form_blood_group")),
            )
            pregnancy = st.selectbox(
                "Pregnancy status",
                options=list(PREGNANCY_OPTIONS),
                index=_option_index(PREGNANCY_OPTIONS, st.session_state.get("form_pregnancy")),
                help="Choose the option that fits. The app does not infer this.",
            )

        h1, h2 = st.columns(2)
        with h1:
            height_cm = st.text_input(
                "Height in cm (optional)",
                value=st.session_state.get("form_height", ""),
            )
        with h2:
            weight_kg = st.text_input(
                "Weight in kg (optional)",
                value=st.session_state.get("form_weight", ""),
            )

        _section("02", "Symptoms", "Select common symptoms and/or describe them in your own words.")
        symptoms = st.multiselect(
            "Common symptoms",
            options=list(COMMON_SYMPTOMS),
            default=st.session_state.get("form_symptoms", []),
            help="You may select more than one.",
        )
        free_text = st.text_area(
            "Describe other symptoms or add detail",
            value=st.session_state.get("form_free_text", ""),
            placeholder="Example: mild scratchy throat and a runny nose after a cold office...",
        )
        d1, d2 = st.columns(2)
        with d1:
            duration = st.selectbox(
                "How long have the symptoms lasted?",
                options=list(DURATION_OPTIONS),
                index=_option_index(DURATION_OPTIONS, st.session_state.get("form_duration")),
            )
            onset = st.selectbox(
                "How did the symptoms start?",
                options=list(ONSET_OPTIONS),
                index=_option_index(ONSET_OPTIONS, st.session_state.get("form_onset")),
            )
        with d2:
            severity = st.slider(
                "How severe do the symptoms feel to you?",
                min_value=1,
                max_value=10,
                value=int(st.session_state.get("form_severity", 3)),
                help="Your own perception, not a clinical score.",
            )
            temperature = st.text_input(
                "Temperature if you measured it",
                value=st.session_state.get("form_temperature", ""),
                placeholder="Optional, for example 38.2 C",
            )
        st.caption("Severity is a personal rating, not a medical score.")
        pain_location = st.text_input(
            "If there is pain, where is it?",
            value=st.session_state.get("form_pain_location", ""),
            placeholder="Optional, for example left side of the head",
        )
        better_with = st.text_input(
            "What seems to make it a little better?",
            value=st.session_state.get("form_better", ""),
        )
        worse_with = st.text_input(
            "What seems to make it worse?",
            value=st.session_state.get("form_worse", ""),
        )
        activity_impact = st.selectbox(
            "How much are usual activities affected?",
            options=list(ACTIVITY_IMPACT_OPTIONS),
            index=_option_index(ACTIVITY_IMPACT_OPTIONS, st.session_state.get("form_activity")),
        )

        _section("03", "Daily context", "Optional lifestyle details. Leave any item blank or on prefer-not-to-say.")
        l1, l2, l3 = st.columns(3)
        with l1:
            sleep_quality = st.selectbox(
                "Sleep last night",
                options=list(SLEEP_OPTIONS),
                index=_option_index(SLEEP_OPTIONS, st.session_state.get("form_sleep")),
            )
        with l2:
            smoking = st.selectbox(
                "Smoking or vaping",
                options=list(SMOKING_OPTIONS),
                index=_option_index(SMOKING_OPTIONS, st.session_state.get("form_smoking")),
            )
        with l3:
            travel = st.selectbox(
                "Recent travel",
                options=list(TRAVEL_OPTIONS),
                index=_option_index(TRAVEL_OPTIONS, st.session_state.get("form_travel")),
            )
        sick_contact = st.selectbox(
            "Contact with someone who was unwell",
            options=list(CONTACT_OPTIONS),
            index=_option_index(CONTACT_OPTIONS, st.session_state.get("form_contact")),
        )
        similar_episode = st.text_input(
            "Have you had something similar before?",
            value=st.session_state.get("form_similar", ""),
            placeholder="Optional",
        )

        _section("04", "Background", "Optional. The app will not prescribe or tell you to stop treatment.")
        medical_conditions = st.text_area(
            "Existing medical conditions",
            value=st.session_state.get("form_conditions", ""),
        )
        allergies = st.text_area(
            "Known allergies",
            value=st.session_state.get("form_allergies", ""),
        )
        medications = st.text_area(
            "Current medications",
            value=st.session_state.get("form_medications", ""),
        )
        additional_notes = st.text_area(
            "Additional notes",
            value=st.session_state.get("form_notes", ""),
        )

        default_lang = st.session_state.get("default_language", "English")
        language = st.selectbox(
            "Response language for the educational explanation",
            options=list(RESPONSE_LANGUAGES),
            index=_option_index(RESPONSE_LANGUAGES, default_lang),
            help="The model is asked to write in this language. Translation quality is not guaranteed.",
        )
        st.caption("Emergency warnings stay prominent even when Urdu is selected.")

        submitted = st.form_submit_button(
            "Generate educational assessment",
            type="primary",
            width="stretch",
        )

    if not submitted:
        educational_note()
        return

    extra_details = {
        "Preferred name": preferred_name,
        "City or area": city,
        "Blood group": blood_group,
        "Pregnancy status": pregnancy,
        "Height in cm": height_cm,
        "Weight in kg": weight_kg,
        "Symptom onset": onset,
        "Measured temperature": temperature,
        "Pain location": pain_location,
        "Seems better with": better_with,
        "Seems worse with": worse_with,
        "Activity impact": activity_impact,
        "Sleep last night": sleep_quality,
        "Smoking or vaping": smoking,
        "Recent travel": travel,
        "Contact with someone unwell": sick_contact,
        "Similar episode before": similar_episode,
        "Known allergies": allergies,
    }

    st.session_state.form_name = preferred_name
    st.session_state.form_age = age
    st.session_state.form_gender = gender
    st.session_state.form_city = city
    st.session_state.form_blood_group = blood_group
    st.session_state.form_pregnancy = pregnancy
    st.session_state.form_height = height_cm
    st.session_state.form_weight = weight_kg
    st.session_state.form_symptoms = symptoms
    st.session_state.form_free_text = free_text
    st.session_state.form_duration = duration
    st.session_state.form_onset = onset
    st.session_state.form_severity = severity
    st.session_state.form_temperature = temperature
    st.session_state.form_pain_location = pain_location
    st.session_state.form_better = better_with
    st.session_state.form_worse = worse_with
    st.session_state.form_activity = activity_impact
    st.session_state.form_sleep = sleep_quality
    st.session_state.form_smoking = smoking
    st.session_state.form_travel = travel
    st.session_state.form_contact = sick_contact
    st.session_state.form_similar = similar_episode
    st.session_state.form_conditions = medical_conditions
    st.session_state.form_allergies = allergies
    st.session_state.form_medications = medications
    st.session_state.form_notes = additional_notes
    st.session_state.form_language = language

    form_data = {
        "age": age,
        "gender": gender,
        "symptoms": symptoms,
        "free_text_symptoms": free_text,
        "duration": duration,
        "severity": severity,
        "medical_conditions": medical_conditions,
        "medications": medications,
        "additional_notes": additional_notes,
        "response_language": language,
        "extra_details": extra_details,
    }

    validation = validate_patient_input(**form_data)
    if not validation.ok:
        for message in validation.errors:
            st.warning(message, icon=":material/warning:")
        return

    fingerprint = fingerprint_payload(
        {
            "age": age,
            "gender": gender,
            "symptoms": symptoms,
            "free_text": free_text,
            "duration": duration,
            "severity": severity,
            "language": language,
            "extra": extra_details,
        }
    )
    if (
        not force_new
        and fingerprint == st.session_state.get("last_submission_hash")
        and st.session_state.get("last_outcome")
    ):
        st.info(
            "These details match the assessment you just ran. "
            "Showing the previous result to avoid a duplicate request. "
            "Tick 'Force a new model request' if you want to send it again.",
            icon=":material/info:",
        )
        st.session_state.current_page = PAGE_RESULTS
        st.rerun()

    extra_text = " ".join(str(value) for value in extra_details.values() if str(value).strip())
    safety = run_safety_only(
        symptoms=symptoms,
        free_text_symptoms=free_text,
        additional_notes=f"{additional_notes} {extra_text}".strip(),
    )
    if safety.possible_emergency:
        extra = safety.urdu_warning_message if language == "Urdu" else ""
        emergency_banner(safety.warning_message, extra)
        st.session_state.emergency_alert = safety.warning_message

    if st.session_state.get("assessment_in_progress"):
        st.info("An assessment is already in progress. Please wait.", icon=":material/hourglass:")
        return
    st.session_state.assessment_in_progress = True

    try:
        with st.spinner("Organising your details and requesting educational information..."):
            outcome = run_assessment(
                form_data,
                save_history=bool(st.session_state.get("history_enabled")),
            )
    finally:
        st.session_state.assessment_in_progress = False

    st.session_state.last_submission_hash = fingerprint
    st.session_state.last_outcome = outcome.to_session_dict()
    st.session_state.streamed_explanation = None
    st.session_state.current_page = PAGE_RESULTS
    st.rerun()
