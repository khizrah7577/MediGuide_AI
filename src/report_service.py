"""
PDF report generation for MediGuide AI.

The PDF is an educational summary. It is not a diagnosis,
medical certificate, or official clinical document.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.config import APP_NAME, APP_TAGLINE, MEDICAL_DISCLAIMER
from src.utils import format_display_datetime

TEAL = colors.HexColor("#0E7490")
NAVY = colors.HexColor("#0F172A")
AMBER = colors.HexColor("#B45309")
RED = colors.HexColor("#B91C1C")
LIGHT = colors.HexColor("#F4F8FB")
LINE = colors.HexColor("#CBD5E1")

WINDOWS_FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\tahoma.ttf"),
    Path(r"C:\Windows\Fonts\arial.ttf"),
    Path(r"C:\Windows\Fonts\seguiui.ttf"),
    Path(r"C:\Windows\Fonts\Nirmala.ttf"),
)

_FONT_REGISTERED = False
_UNICODE_FONT = "Helvetica"


def _register_unicode_font() -> str:
    """Try to register a Windows font that can draw Arabic/Urdu glyphs."""
    global _FONT_REGISTERED, _UNICODE_FONT
    if _FONT_REGISTERED:
        return _UNICODE_FONT
    for candidate in WINDOWS_FONT_CANDIDATES:
        if candidate.exists():
            try:
                pdfmetrics.registerFont(TTFont("MediGuideUnicode", str(candidate)))
                _UNICODE_FONT = "MediGuideUnicode"
                _FONT_REGISTERED = True
                return _UNICODE_FONT
            except Exception:
                continue
    _FONT_REGISTERED = True
    _UNICODE_FONT = "Helvetica"
    return _UNICODE_FONT


def _reshape_if_needed(text: str, language: str) -> str:
    """
    Best-effort Urdu shaping. If shaping libraries or fonts are missing,
    the PDF still builds and includes a notice instead of crashing.
    """
    if not text:
        return ""
    if language != "Urdu":
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    try:
        import arabic_reshaper

        try:
            from bidi.algorithm import get_display
        except ImportError:
            from bidi import get_display

        reshaped = arabic_reshaper.reshape(text)
        display = get_display(reshaped)
        return (
            display.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
    except Exception:
        return escaped


def _styles(font_name: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "MGTitle",
            parent=base["Title"],
            fontName=font_name,
            fontSize=18,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=0,
            leading=22,
        ),
        "tagline": ParagraphStyle(
            "MGTagline",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=9,
            textColor=colors.white,
            alignment=TA_LEFT,
            leading=12,
        ),
        "heading": ParagraphStyle(
            "MGHeading",
            parent=base["Heading2"],
            fontName=font_name,
            fontSize=12,
            textColor=TEAL,
            spaceBefore=12,
            spaceAfter=6,
            leading=16,
        ),
        "body": ParagraphStyle(
            "MGBody",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=10,
            textColor=NAVY,
            alignment=TA_JUSTIFY,
            leading=14,
            spaceAfter=6,
        ),
        "center_note": ParagraphStyle(
            "MGNote",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=9,
            textColor=RED,
            alignment=TA_CENTER,
            leading=12,
            spaceAfter=8,
        ),
        "disclaimer": ParagraphStyle(
            "MGDisclaimer",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=8,
            textColor=NAVY,
            alignment=TA_JUSTIFY,
            leading=11,
        ),
        "meta": ParagraphStyle(
            "MGMeta",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=9,
            textColor=NAVY,
            alignment=TA_LEFT,
            leading=12,
        ),
        "right_meta": ParagraphStyle(
            "MGRightMeta",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=9,
            textColor=colors.white,
            alignment=TA_RIGHT,
            leading=12,
        ),
    }


def _bullet_list(items: list[str], styles: dict[str, ParagraphStyle], language: str) -> ListFlowable | Paragraph:
    cleaned = [item.strip() for item in items if str(item).strip()]
    if not cleaned:
        return Paragraph(_reshape_if_needed("None recorded.", language), styles["body"])
    flow_items = [
        ListItem(Paragraph(_reshape_if_needed(item, language), styles["body"]), leftIndent=8)
        for item in cleaned
    ]
    return ListFlowable(flow_items, bulletType="bullet", start="•", leftIndent=12)


def build_pdf_report(
    *,
    patient: dict[str, Any],
    structured: dict[str, Any],
    timestamp: str,
    safety: dict[str, Any] | None = None,
    include_personal: bool = True,
) -> bytes:
    """
    Create a PDF and return the file bytes for Streamlit download_button.
    """
    font_name = _register_unicode_font()
    language = patient.get("response_language") or "English"
    styles = _styles(font_name)
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title=f"{APP_NAME} educational summary",
        author=APP_NAME,
    )

    story: list[Any] = []
    header = Table(
        [[
            Paragraph(f"<b>{APP_NAME}</b><br/>{APP_TAGLINE}", styles["title"]),
            Paragraph("EDUCATIONAL ONLY<br/>Not a diagnosis", styles["right_meta"]),
        ]],
        colWidths=[4.6 * inch, 2.2 * inch],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), TEAL),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "This document is not a medical certificate, prescription, or confirmed diagnosis.",
            styles["center_note"],
        )
    )

    story.append(Paragraph("Assessment details", styles["heading"]))
    meta_lines = [
        f"Generated: {format_display_datetime(timestamp)}",
        f"Response language requested: {language}",
        f"Urgency category (educational label only): {structured.get('urgency_level', 'Unknown')}",
    ]
    if include_personal:
        meta_lines.extend(
            [
                f"Age: {patient.get('age', 'Not provided')}",
                f"Gender (user-selected): {patient.get('gender', 'Not provided')}",
                f"Symptoms: {patient.get('symptoms', 'Not provided')}",
                f"Duration: {patient.get('duration', 'Not provided')}",
                f"Perceived severity (user rating 1-10, not a clinical score): {patient.get('severity', 'Not provided')}",
            ]
        )
        story.append(
            Paragraph(
                "This report includes the symptom details entered for this session. "
                "Do not share it as an official patient record.",
                styles["body"],
            )
        )
    for line in meta_lines:
        story.append(Paragraph(_reshape_if_needed(line, language), styles["meta"]))

    if safety and safety.get("possible_emergency"):
        story.append(Paragraph("Possible emergency warning", styles["heading"]))
        story.append(
            Paragraph(
                _reshape_if_needed(safety.get("warning_message") or "", language),
                styles["body"],
            )
        )

    story.append(Paragraph("General educational information", styles["heading"]))
    story.append(Paragraph(_reshape_if_needed(structured.get("summary") or "", language), styles["body"]))

    story.append(Paragraph("Possible conditions to discuss — not confirmed diagnoses", styles["heading"]))
    conditions = structured.get("possible_conditions") or []
    if not conditions:
        story.append(Paragraph("No possible conditions were listed.", styles["body"]))
    for item in conditions:
        name = item.get("name", "Unnamed possibility")
        reason = item.get("reason", "")
        story.append(
            Paragraph(
                _reshape_if_needed(f"<b>{name}</b> — {reason}", language),
                styles["body"],
            )
        )

    story.append(Paragraph("Recommended next steps", styles["heading"]))
    story.append(_bullet_list(structured.get("recommended_next_steps") or [], styles, language))

    story.append(Paragraph("Questions for a healthcare professional", styles["heading"]))
    story.append(_bullet_list(structured.get("questions_for_doctor") or [], styles, language))

    story.append(Paragraph("Warning signs", styles["heading"]))
    story.append(_bullet_list(structured.get("warning_signs") or [], styles, language))

    if language == "Urdu" and font_name == "Helvetica":
        story.append(Paragraph("Urdu font notice", styles["heading"]))
        story.append(
            Paragraph(
                "A Unicode font with Arabic-script support was not found on this computer, "
                "so Urdu characters may not display correctly in this PDF.",
                styles["body"],
            )
        )

    story.append(Spacer(1, 8))
    disclaimer_table = Table(
        [[Paragraph(_reshape_if_needed(MEDICAL_DISCLAIMER, "English"), styles["disclaimer"])]],
        colWidths=[6.8 * inch],
    )
    disclaimer_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 1, AMBER),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(disclaimer_table)

    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(TEAL)
        canvas.rect(0, 0, A4[0], 28, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(40, 12, f"{APP_NAME} educational summary — not a medical diagnosis")
        canvas.drawRightString(A4[0] - 40, 12, f"Page {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
