"""Schlankes PDF für einen erledigten To-do-Abschluss — kein Tagesbericht."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.site_tasks import completion_summary_for
from report_export import (
    GREY_META_HEX,
    LINE_HEX,
    SECTION_HEX,
    SOFT_BG_HEX,
    TEXT_DARK_HEX,
    _format_date_de,
    _logo_image_for_pdf,
    _resolve_logo_path,
    _xml_para_text,
    sanitize_export_slug,
    sanitize_export_slug_ascii,
)


def build_task_completion_attachment_names(task: dict[str, Any]) -> tuple[str, str]:
    site = sanitize_export_slug_ascii(str(task.get("projectName") or "Baustelle")).lower()
    day = sanitize_export_slug_ascii(str(task.get("dueDate") or "datum")).lower()
    ascii_nm = f"aufgabenabschluss_{site}_{day}.pdf"
    desc = (
        f"aufgabenabschluss_{sanitize_export_slug(str(task.get('projectName') or 'Baustelle'))}_"
        f"{sanitize_export_slug(str(task.get('dueDate') or 'datum'))}.pdf"
    )
    return ascii_nm, desc


def build_task_completion_pdf_bytes(
    task: dict[str, Any],
    company_profile: dict[str, Any],
    *,
    resolve_logo: Any = None,
) -> bytes:
    buf = BytesIO()
    doc_tpl = SimpleDocTemplate(
        buf,
        pagesize=A4,
        title="Aufgabenabschluss",
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.8 * cm,
    )
    styles = getSampleStyleSheet()
    meta_style = ParagraphStyle(
        name="TaskCompMeta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=GREY_META_HEX,
        spaceAfter=1,
        leading=11,
    )
    body_style = ParagraphStyle(
        name="TaskCompBody",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        textColor=TEXT_DARK_HEX,
    )
    title_style = ParagraphStyle(
        name="TaskCompTitle",
        parent=styles["Heading1"],
        fontSize=15,
        textColor=TEXT_DARK_HEX,
        spaceBefore=4,
        spaceAfter=6,
        alignment=1,
        fontName="Helvetica-Bold",
    )
    company_style = ParagraphStyle(
        name="TaskCompCompany",
        parent=styles["Heading1"],
        fontSize=13,
        textColor=TEXT_DARK_HEX,
        spaceAfter=2,
        fontName="Helvetica-Bold",
    )
    section_head = ParagraphStyle(
        name="TaskCompSection",
        parent=styles["Heading2"],
        fontSize=10.5,
        textColor=SECTION_HEX,
        spaceBefore=10,
        spaceAfter=4,
        leading=13,
        fontName="Helvetica-Bold",
    )
    section_text_style = ParagraphStyle(
        name="TaskCompSectionBody",
        parent=body_style,
        spaceAfter=4,
    )
    info_label_style = ParagraphStyle(
        name="TaskCompInfoLabel",
        parent=meta_style,
        fontName="Helvetica-Bold",
        textColor=SECTION_HEX,
    )
    info_value_style = ParagraphStyle(
        name="TaskCompInfoValue",
        parent=body_style,
        fontSize=9.2,
    )

    emails = str(company_profile.get("officeEmail") or "")
    phone = str(company_profile.get("phone") or "")
    company_name = str(company_profile.get("companyName") or "Firma")
    proj = str(task.get("projectName") or "—").strip() or "—"
    datum = _format_date_de(str(task.get("dueDate") or "—"))
    names = [str(x).strip() for x in (task.get("assigneeNames") or []) if str(x).strip()]
    mitarbeiter = ", ".join(names) if names else "Keine Angabe"
    summary = completion_summary_for(task) or "Keine Angabe"

    def footer(canv: Any, __: Any) -> None:
        canv.saveState()
        canv.setFont("Helvetica", 7)
        canv.setFillColor(GREY_META_HEX)
        canv.drawCentredString(A4[0] / 2.0, 1.2 * cm, "Erstellt mit Freiraum Baustellen-Doku")
        canv.restoreState()

    story: list[Any] = []
    logo_path = _resolve_logo_path(task, company_profile, resolve_logo=resolve_logo)
    logo_img = _logo_image_for_pdf(logo_path, max_width_cm=5.0, max_height_cm=2.9) if logo_path else None

    company_lines: list[Any] = [Paragraph(_xml_para_text(company_name), company_style)]
    if emails:
        company_lines.append(Paragraph(_xml_para_text(f"Büro-E-Mail: {emails}"), meta_style))
    if phone:
        company_lines.append(Paragraph(_xml_para_text(f"Telefon: {phone}"), meta_style))

    if logo_img:
        head_tbl = Table(
            [[logo_img, company_lines]],
            colWidths=[doc_tpl.width * 0.30, doc_tpl.width * 0.70],
        )
    else:
        head_tbl = Table([[company_lines]], colWidths=[doc_tpl.width])
    head_tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(head_tbl)
    story.append(Spacer(1, 3))
    story.append(Paragraph("AUFGABENABSCHLUSS", title_style))
    story.append(Spacer(1, 4))
    line_tbl = Table([[""]], colWidths=[doc_tpl.width], rowHeights=[1.2])
    line_tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LINE_HEX)]))
    story.append(line_tbl)
    story.append(Spacer(1, 8))

    meta_rows = [
        [Paragraph("Baustelle", info_label_style), Paragraph(_xml_para_text(proj), info_value_style)],
        [Paragraph("Datum", info_label_style), Paragraph(_xml_para_text(datum), info_value_style)],
        [Paragraph("Mitarbeitende", info_label_style), Paragraph(_xml_para_text(mitarbeiter), info_value_style)],
    ]
    tbl = Table(meta_rows, colWidths=[doc_tpl.width * 0.30, doc_tpl.width * 0.70])
    tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, -1), SOFT_BG_HEX),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE_HEX),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE_HEX),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(tbl)
    story.append(Spacer(1, 10))
    story.append(Paragraph(_xml_para_text("Zusammenfassung"), section_head))
    story.append(Paragraph(_xml_para_text(summary), section_text_style))

    doc_tpl.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
