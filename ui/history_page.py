"""
Optional local assessment history.
"""

from __future__ import annotations

import streamlit as st

from src.config import PAGE_RESULTS
from src.history_service import clear_all_history, delete_assessment, get_assessment, list_assessments
from src.utils import format_display_datetime
from ui.components import disclaimer_box, render_page_intro, show_urgency_badge, urgency_pill


def render_history_page() -> None:
    render_page_intro(
        "Visit history",
        "Stored only on this computer, and only if you enable it. This prototype does not have secure patient accounts.",
        icon=":material/history:",
    )
    st.write(
        "Do not store identifiable real patient records here. "
        "Medications and extra notes are not saved."
    )
    disclaimer_box()

    enabled = st.toggle(
        "Enable local assessment history",
        value=bool(st.session_state.get("history_enabled", False)),
        help="When on, new assessments can be saved without medications or extra notes.",
    )
    st.session_state.history_enabled = enabled

    if not enabled:
        st.info(
            "History is off. Turn it on if you want this educational prototype to "
            "remember assessments on this device. Stored fields: time, age, gender, "
            "symptoms, duration, severity, language, urgency, and educational JSON.",
            icon=":material/info:",
        )
        return

    records = list_assessments()
    if not records:
        with st.container(border=True):
            st.subheader("No visits saved yet")
            st.write("When you generate an assessment with history enabled, it will appear here.")
        return

    st.badge(f"{len(records)} saved visits", icon=":material/folder:", color="blue")
    confirm_clear = st.checkbox("I understand this will delete all local history")
    if st.button("Clear all history", icon=":material/delete:", disabled=not confirm_clear):
        clear_all_history()
        st.success("All local history was deleted.", icon=":material/check_circle:")
        st.rerun()

    for record in records:
        with st.expander(
            f"{format_display_datetime(record.get('created_at'))} · "
            f"{record.get('symptoms') or 'No symptom text'} · "
            f"{record.get('urgency_level') or 'Unknown'}"
        ):
            show_urgency_badge(str(record.get("urgency_level") or ""))
            st.markdown(urgency_pill(record.get("urgency_level") or ""), unsafe_allow_html=True)
            st.write(f"**Age:** {record.get('age')}")
            st.write(f"**Gender:** {record.get('gender')}")
            st.write(f"**Duration:** {record.get('duration')}")
            st.write(f"**Severity:** {record.get('severity')}")
            st.write(record.get("summary") or "")
            with st.container(horizontal=True):
                if st.button("Open full result", icon=":material/clinical_notes:", key=f"open_{record['id']}"):
                    full = get_assessment(record["id"])
                    if full:
                        st.session_state.last_outcome = {
                            "success": True,
                            "assessment_id": full["id"],
                            "timestamp": full.get("created_at"),
                            "patient": {
                                "age": full.get("age"),
                                "gender": full.get("gender"),
                                "symptoms": full.get("symptoms"),
                                "duration": full.get("duration"),
                                "severity": full.get("severity"),
                                "response_language": full.get("response_language"),
                            },
                            "structured": full.get("structured") or {},
                            "safety": {
                                "possible_emergency": (full.get("urgency_level") == "EMERGENCY"),
                                "matched_signs": [],
                                "warning_message": "",
                                "urdu_warning_message": "",
                                "incomplete_list_note": "",
                            },
                            "parse_notes": ["Opened from local history."],
                            "error": None,
                            "skipped_model": True,
                            "model_called": False,
                        }
                        st.session_state.streamed_explanation = None
                        st.session_state.current_page = PAGE_RESULTS
                        st.rerun()
                if st.button("Delete this assessment", icon=":material/delete:", key=f"del_{record['id']}"):
                    delete_assessment(record["id"])
                    st.rerun()
