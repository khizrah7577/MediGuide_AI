"""
Results dashboard for a completed educational assessment.
Presented in a clinic-chat layout so the visit feels like a consultation.
"""

from __future__ import annotations

import streamlit as st

from src.assessment_service import build_explanation_stream
from src.chains import classify_llm_error
from src.config import MEDICAL_DISCLAIMER, PAGE_ASSESSMENT, PAGE_CHAT, has_api_key
from src.report_service import build_pdf_report
from ui.components import (
    disclaimer_box,
    educational_note,
    emergency_banner,
    render_page_intro,
    render_structured_chat_cards,
    show_urgency_badge,
    urgency_pill,
)


def render_results_dashboard() -> None:
    render_page_intro(
        "Consultation results",
        "Educational information from this visit. This is not a diagnosis or medical certificate.",
        icon=":material/clinical_notes:",
    )
    outcome = st.session_state.get("last_outcome")

    if not outcome:
        with st.container(border=True):
            st.subheader("No consultation yet")
            st.write("Complete medical chat or the symptom form to see results here.")
            with st.container(horizontal=True):
                if st.button("Open medical chat", type="primary", icon=":material/stethoscope:"):
                    st.session_state.current_page = PAGE_CHAT
                    st.rerun()
                if st.button("Open symptom form", icon=":material/assignment:"):
                    st.session_state.current_page = PAGE_ASSESSMENT
                    st.rerun()
        disclaimer_box()
        return

    safety = outcome.get("safety") or {}
    if safety.get("possible_emergency"):
        extra = safety.get("urdu_warning_message") or ""
        emergency_banner(safety.get("warning_message") or "", extra)
        st.caption(safety.get("incomplete_list_note", ""))

    if outcome.get("error") and not outcome.get("structured"):
        st.error(outcome["error"], icon=":material/error:")
        if st.button("Try the form again", icon=":material/refresh:"):
            st.session_state.current_page = PAGE_ASSESSMENT
            st.rerun()
        disclaimer_box()
        return

    if outcome.get("error") and outcome.get("structured"):
        st.warning(outcome["error"], icon=":material/warning:")

    structured = outcome.get("structured") or {}
    patient = outcome.get("patient") or {}
    urgency = structured.get("urgency_level", "MEDIUM")

    show_urgency_badge(urgency)
    st.markdown(urgency_pill(urgency), unsafe_allow_html=True)
    if urgency == "LOW":
        st.info(
            "A LOW label is only a visual category for education. "
            "It does not mean the symptoms are harmless or that anyone is safe.",
            icon=":material/info:",
        )
    elif urgency == "MEDIUM":
        st.warning("This caution label is educational, not a clinical triage result.", icon=":material/warning:")
    elif urgency == "HIGH":
        st.error("This high-caution label is educational. Seek prompt in-person medical advice.", icon=":material/priority_high:")
    elif urgency == "EMERGENCY":
        st.error("Emergency-style label: seek emergency care now. Do not wait on this app.", icon=":material/emergency:")

    c1, c2, c3 = st.columns(3)
    c1.metric("Urgency category", urgency, help="Visual label only. Not a validated triage score.")
    c2.metric("Perceived severity", f"{patient.get('severity', '—')}/10")
    c3.metric("Duration", patient.get("duration", "—"))

    with st.chat_message("user", avatar=":material/person:"):
        st.markdown("**Patient symptom summary**")
        st.write(f"Age: {patient.get('age', 'Not provided')}")
        st.write(f"Gender (user-selected): {patient.get('gender', 'Not provided')}")
        st.write(f"Symptoms: {patient.get('symptoms', 'Not provided')}")
        extra = patient.get("extra_context") or ""
        if extra and extra != "Not provided":
            with st.expander("Additional intake details"):
                st.write(extra)
        st.caption("Medications and extra notes are not repeated in the main summary.")

    with st.chat_message("assistant", avatar=":material/stethoscope:"):
        st.markdown("**Educational consultation note**")
        st.caption("This is general information to discuss with a clinician. It is not a confirmed diagnosis.")
        render_structured_chat_cards(structured)
        for note in outcome.get("parse_notes") or []:
            st.caption(note)
        if outcome.get("skipped_model"):
            st.info(
                "The model was not called for this result. Any warning above came from local safety rules.",
                icon=":material/policy:",
            )

        can_stream = (
            bool(outcome.get("model_called"))
            and bool(structured)
            and (has_api_key() or bool(st.session_state.get("openai_api_key_override")))
        )
        st.markdown("**Live explanation stream**")
        st.caption(
            "The streamed explanation is a second model call. "
            "It is not the same request that produced the JSON fields above."
        )
        if not can_stream:
            st.info("Streaming is unavailable because the model was not called for this assessment.", icon=":material/info:")
        elif st.session_state.get("streamed_explanation"):
            st.write(st.session_state.streamed_explanation)
        else:
            try:
                generator = build_explanation_stream(patient, structured)
                st.session_state.streamed_explanation = st.write_stream(generator)
            except Exception as exc:
                st.warning(classify_llm_error(exc), icon=":material/warning:")
                st.session_state.streamed_explanation = ""

    tabs = st.tabs(
        [
            ":material/menu_book: Educational information",
            ":material/symptoms: Possible conditions",
            ":material/checklist: Next steps",
            ":material/quiz: Questions for a clinician",
            ":material/warning: Warning signs",
        ]
    )

    with tabs[0]:
        st.write(structured.get("summary") or "No summary was available.")
    with tabs[1]:
        st.caption("These are possibilities to discuss. They are not confirmed diagnoses.")
        conditions = structured.get("possible_conditions") or []
        if not conditions:
            st.write("No possible conditions were listed.")
        for item in conditions:
            with st.expander(item.get("name") or "Unnamed possibility"):
                st.write(item.get("reason") or "")
                st.caption("Uncertain educational information only.")
    with tabs[2]:
        steps = structured.get("recommended_next_steps") or []
        if not steps:
            st.write("No next steps were listed.")
        for step in steps:
            st.markdown(f"- {step}")
    with tabs[3]:
        questions = structured.get("questions_for_doctor") or []
        if not questions:
            st.write("No questions were listed.")
        for question in questions:
            st.markdown(f"- {question}")
    with tabs[4]:
        warnings = structured.get("warning_signs") or []
        if not warnings:
            st.write("No extra warning signs were listed. This does not mean an emergency is absent.")
        for warning in warnings:
            st.markdown(f"- {warning}")

    st.subheader("PDF visit summary")
    st.caption(
        "The PDF is labelled as educational and is not a medical certificate. "
        "It includes the symptom summary from this session."
    )
    try:
        pdf_bytes = build_pdf_report(
            patient=patient,
            structured=structured,
            timestamp=outcome.get("timestamp") or "",
            safety=safety,
            include_personal=True,
        )
        st.download_button(
            "Download educational PDF summary",
            data=pdf_bytes,
            file_name=f"mediguide_educational_summary_{outcome.get('assessment_id', 'report')}.pdf",
            mime="application/pdf",
            type="primary",
            icon=":material/download:",
        )
    except Exception:
        st.warning(
            "The PDF could not be created on this computer. You can still copy the on-screen results.",
            icon=":material/warning:",
        )

    with st.container(horizontal=True):
        if st.button("Continue in medical chat", type="primary", icon=":material/stethoscope:"):
            st.session_state.current_page = PAGE_CHAT
            st.rerun()
        if st.button("Start another form", icon=":material/assignment:"):
            st.session_state.current_page = PAGE_ASSESSMENT
            st.rerun()

    disclaimer_box()
    educational_note()
    st.caption(MEDICAL_DISCLAIMER)
