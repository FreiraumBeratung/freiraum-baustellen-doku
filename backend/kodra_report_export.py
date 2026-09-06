"""PDF-Export mit Kodra-Briefpapier — nur nach is_kodra_export().

Inhalt (Abschnitte) entspricht dem Freiraum-Standard; Rahmen = Kunden-Briefkopf.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from kodra_letterhead import (
    KODRA_BOTTOM_MARGIN,
    KODRA_LEFT_MARGIN,
    KODRA_NAVY,
    KODRA_RIGHT_MARGIN,
    KODRA_TOP_MARGIN,
    draw_kodra_letterhead,
)
from report_export import (
    LINE_HEX,
    SECTION_HEX,
    SOFT_BG_HEX,
    TEXT_DARK_HEX,
    GREY_META_HEX,
    _append_pdf_signatures,
    _employee_hours_lines_for_report,
    _format_date_de,
    _list_or_keine,
    _protocol_body_paragraphs,
    _structured,
    _xml_para_text,
    _zeitraum_label,
    _fmt_hours,
    format_arbeitszeit_with_hours,
)


class _KodraCanvas(pdf_canvas.Canvas):
    """Speichert Seiten und zeichnet Briefkopf inkl. ‚Seite X von Y‘ beim Speichern."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._kodra_states: list[dict[str, Any]] = []

    def showPage(self) -> None:  # noqa: N802
        self._kodra_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._kodra_states)
        for state in self._kodra_states:
            self.__dict__.update(state)
            page_no = int(getattr(self, "_pageNumber", 1) or 1)

            class _Doc:
                pass

            doc = _Doc()
            doc.page = page_no
            doc.page_count = total
            draw_kodra_letterhead(self, doc)
            super().showPage()
        super().save()


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "meta": ParagraphStyle(
            name="KodraMeta",
            parent=base["Normal"],
            fontSize=9,
            textColor=GREY_META_HEX,
            spaceAfter=1,
            leading=11,
        ),
        "body": ParagraphStyle(
            name="KodraBody",
            parent=base["Normal"],
            fontSize=9.5,
            leading=13,
            textColor=TEXT_DARK_HEX,
        ),
        "section": ParagraphStyle(
            name="KodraSection",
            parent=base["Heading2"],
            fontSize=10.5,
            textColor=KODRA_NAVY,
            spaceBefore=10,
            spaceAfter=4,
            leading=13,
            fontName="Helvetica-Bold",
        ),
        "title": ParagraphStyle(
            name="KodraTitle",
            parent=base["Heading1"],
            fontSize=14,
            textColor=KODRA_NAVY,
            spaceBefore=2,
            spaceAfter=6,
            alignment=0,
            fontName="Helvetica-Bold",
        ),
        "label": ParagraphStyle(
            name="KodraLabel",
            parent=base["Normal"],
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=SECTION_HEX,
            leading=11,
        ),
        "value": ParagraphStyle(
            name="KodraValue",
            parent=base["Normal"],
            fontSize=9.2,
            leading=12,
            textColor=TEXT_DARK_HEX,
        ),
        "bullet": ParagraphStyle(
            name="KodraBullet",
            parent=base["Normal"],
            fontSize=9.5,
            leading=13,
            textColor=TEXT_DARK_HEX,
            leftIndent=10,
            spaceAfter=3,
        ),
        "section_text": ParagraphStyle(
            name="KodraSectionText",
            parent=base["Normal"],
            fontSize=9.5,
            leading=13,
            textColor=TEXT_DARK_HEX,
            spaceAfter=4,
        ),
        "betreff_label": ParagraphStyle(
            name="KodraBetreffLabel",
            parent=base["Normal"],
            fontSize=9,
            textColor=GREY_META_HEX,
            leading=11,
        ),
        "betreff_value": ParagraphStyle(
            name="KodraBetreffValue",
            parent=base["Normal"],
            fontSize=10,
            fontName="Helvetica-Bold",
            textColor=TEXT_DARK_HEX,
            leading=12,
        ),
    }


def _new_doc(buf: BytesIO, title: str) -> SimpleDocTemplate:
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        title=title,
        leftMargin=KODRA_LEFT_MARGIN,
        rightMargin=KODRA_RIGHT_MARGIN,
        topMargin=KODRA_TOP_MARGIN,
        bottomMargin=KODRA_BOTTOM_MARGIN,
    )
    return doc


def _betreff_datum_block(
    styles: dict[str, ParagraphStyle],
    *,
    betreff: str,
    datum: str,
    width: float,
) -> Table:
    left = [
        Paragraph("Betreff", styles["betreff_label"]),
        Paragraph(_xml_para_text(betreff), styles["betreff_value"]),
    ]
    right = [
        Paragraph("Datum", styles["betreff_label"]),
        Paragraph(_xml_para_text(datum), styles["betreff_value"]),
    ]
    tbl = Table([[left, right]], colWidths=[width * 0.62, width * 0.38])
    tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return tbl


def _meta_table(rows: list[list[Any]], width: float) -> Table:
    tbl = Table(rows, colWidths=[width * 0.30, width * 0.70])
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
    return tbl


def _finalize(buf: BytesIO, doc_tpl: SimpleDocTemplate, story: list[Any]) -> bytes:
    doc_tpl.build(story, canvasmaker=_KodraCanvas)
    return buf.getvalue()


def build_kodra_report_pdf_bytes(
    report: dict[str, Any],
    company_profile: dict[str, Any],
    *,
    resolve_logo: Any = None,
    resolve_signature: Any = None,
) -> bytes:
    _ = resolve_logo  # Briefkopf nutzt festes Kodra-Logo
    buf = BytesIO()
    doc_tpl = _new_doc(buf, "Tagesbericht")
    styles = _styles()
    st = _structured(report)
    proj = str(report.get("projectName") or "—")
    customer = str(report.get("customerName") or "—")
    datum = _format_date_de(str(report.get("date") or "—"))
    emps_raw = report.get("employees")
    mitarbeiter = (
        ", ".join(str(e) for e in emps_raw) if isinstance(emps_raw, list) and emps_raw else "Keine Angabe"
    )
    zeit = format_arbeitszeit_with_hours(report.get("startTime"), report.get("endTime"))
    summary = str(st.get("summary") or "Keine Angabe")
    acts = _list_or_keine(st.get("activities"))
    mats = _list_or_keine(st.get("materials"))
    machine_hours = _list_or_keine(st.get("machineHours"))
    probs = _list_or_keine(st.get("problems"))
    opens = _list_or_keine(st.get("openItems"))
    ktalk = str(st.get("customerTalk") or "Keine Angabe")

    story: list[Any] = []
    story.append(_betreff_datum_block(styles, betreff=proj, datum=datum, width=doc_tpl.width))
    story.append(Spacer(1, 10))
    story.append(Paragraph("TAGESBERICHT", styles["title"]))
    story.append(Spacer(1, 4))

    meta_rows = [
        [Paragraph("Baustelle", styles["label"]), Paragraph(_xml_para_text(proj), styles["value"])],
        [Paragraph("Kunde", styles["label"]), Paragraph(_xml_para_text(customer), styles["value"])],
        [Paragraph("Datum", styles["label"]), Paragraph(_xml_para_text(datum), styles["value"])],
        [Paragraph("Mitarbeitende", styles["label"]), Paragraph(_xml_para_text(mitarbeiter), styles["value"])],
        [Paragraph("Arbeitszeit", styles["label"]), Paragraph(_xml_para_text(zeit), styles["value"])],
    ]
    story.append(_meta_table(meta_rows, doc_tpl.width))
    story.append(Spacer(1, 10))

    emp_hour_lines = _employee_hours_lines_for_report(report)
    if emp_hour_lines:
        story.append(Paragraph(_xml_para_text("Stunden je Mitarbeiter"), styles["section"]))
        for line in emp_hour_lines:
            story.append(Paragraph(f"\u2022 {_xml_para_text(line)}", styles["bullet"]))
        story.append(Spacer(1, 8))

    def sec(title: str) -> None:
        story.append(Paragraph(_xml_para_text(title), styles["section"]))

    def bullets(items: list[str]) -> None:
        for item in items:
            story.append(Paragraph(f"\u2022 {_xml_para_text(item)}", styles["bullet"]))

    sec("Zusammenfassung")
    story.append(Paragraph(_xml_para_text(summary), styles["section_text"]))
    sec("Tätigkeiten")
    bullets(acts)
    sec("Material")
    bullets(mats)
    sec("Maschinenstunden")
    bullets(machine_hours)
    sec("Probleme")
    bullets(probs)
    sec("Offene Punkte")
    bullets(opens)
    sec("Kundengespräch")
    story.append(Paragraph(_xml_para_text(ktalk), styles["section_text"]))

    _append_pdf_signatures(
        story,
        doc_tpl,
        report,
        section_head=styles["section"],
        info_label_style=styles["label"],
        meta_style=styles["meta"],
        resolve_signature=resolve_signature,
    )
    return _finalize(buf, doc_tpl, story)


def build_kodra_collective_pdf_bytes(
    payload: dict[str, Any],
    company_profile: dict[str, Any],
    *,
    resolve_logo: Any = None,
    resolve_photo: Any = None,
    resolve_signature: Any = None,
) -> bytes:
    """Gesamtbericht im Kodra-Briefpapier — Inhalt wie Standard, Rahmen Kodra."""
    # Foto-/Signatur-Anhänge: Standard-Logik wiederverwenden, indem wir nach dem
    # Briefkopf-Rahmen die bestehende Collective-Story nicht duplizieren wollen.
    # Deshalb: Standard-PDF erzeugen und ist hier bewusst eigene schlanke Variante
    # ohne Foto-Galerie (wie Basis-Inhalt). Fotos bleiben über den Standard-Export
    # der anderen Firmen; für Kodra Priorität = Briefkopf + Kerninhalt.
    _ = (resolve_logo, resolve_photo, resolve_signature, company_profile)
    buf = BytesIO()
    doc_tpl = _new_doc(buf, "Gesamtbericht")
    styles = _styles()
    totals = payload.get("totals", {}) if isinstance(payload.get("totals"), dict) else {}
    proj = str(payload.get("projectName") or "—")
    customer = str(payload.get("customerName") or "—")
    zeitraum = _zeitraum_label(payload)

    story: list[Any] = []
    story.append(_betreff_datum_block(styles, betreff=proj, datum=zeitraum, width=doc_tpl.width))
    story.append(Spacer(1, 10))
    story.append(Paragraph("GESAMTBERICHT", styles["title"]))
    story.append(Spacer(1, 4))
    meta_rows = [
        [Paragraph("Baustelle", styles["label"]), Paragraph(_xml_para_text(proj), styles["value"])],
        [Paragraph("Kunde", styles["label"]), Paragraph(_xml_para_text(customer), styles["value"])],
        [Paragraph("Zeitraum", styles["label"]), Paragraph(_xml_para_text(zeitraum), styles["value"])],
        [Paragraph("Arbeitstage", styles["label"]), Paragraph(_xml_para_text(str(totals.get("reportCount") or 0)), styles["value"])],
        [Paragraph("Gesamtstunden", styles["label"]), Paragraph(_xml_para_text(_fmt_hours(totals.get("totalHours"))), styles["value"])],
    ]
    story.append(_meta_table(meta_rows, doc_tpl.width))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Zusammenfassung", styles["section"]))
    story.append(Paragraph(_xml_para_text(str(payload.get("summary") or "Keine Angabe")), styles["section_text"]))

    hours_by_emp = totals.get("hoursByEmployee") or []
    if hours_by_emp:
        story.append(Paragraph("Stunden je Mitarbeiter", styles["section"]))
        for row in hours_by_emp:
            if isinstance(row, dict):
                story.append(
                    Paragraph(
                        f"\u2022 {_xml_para_text(str(row.get('name') or '—'))}: {_fmt_hours(row.get('hours'))} h",
                        styles["bullet"],
                    )
                )

    for key, title in (
        ("materials", "Material (gesamt)"),
        ("openItems", "Offene Punkte (gesamt)"),
        ("problems", "Probleme (gesamt)"),
        ("activities", "Tätigkeiten (gesamt)"),
    ):
        items = totals.get(key) or []
        if items:
            story.append(Paragraph(title, styles["section"]))
            for item in items:
                story.append(Paragraph(f"\u2022 {_xml_para_text(str(item))}", styles["bullet"]))

    days = payload.get("days") or []
    if days:
        story.append(Paragraph("Tagesverlauf", styles["section"]))
        for day in days:
            if not isinstance(day, dict):
                continue
            emps = day.get("employees") or []
            emps_label = ", ".join(str(e) for e in emps) if emps else "—"
            head = (
                f"{_format_date_de(str(day.get('date') or '—'))} · {emps_label} · "
                f"{_fmt_hours(day.get('hours'))} h"
            )
            story.append(Paragraph(_xml_para_text(head), styles["label"]))
            for a in day.get("activities") or []:
                story.append(Paragraph(f"\u2022 {_xml_para_text(str(a))}", styles["bullet"]))
            note = str(day.get("notes") or "").strip()
            if note:
                story.append(Paragraph(_xml_para_text(f"Besonderheiten: {note}"), styles["meta"]))

    return _finalize(buf, doc_tpl, story)


def build_kodra_protocol_pdf_bytes(
    protocol: dict[str, Any],
    company_profile: dict[str, Any],
    *,
    resolve_logo: Any = None,
    resolve_signature: Any = None,
) -> bytes:
    from app.services.site_protocol import protocol_display_text, protocol_for_pdf_signatures

    _ = resolve_logo
    buf = BytesIO()
    styles = _styles()
    proj = str(protocol.get("projectName") or "—")
    customer = str(protocol.get("customerName") or "—")
    datum = _format_date_de(str(protocol.get("date") or "—"))
    participants = str(protocol.get("participants") or "").strip()
    mode = str(protocol.get("mode") or "quick")
    seq = protocol.get("sequenceNumber")
    if mode == "thoughts":
        doc_title = "GEDANKENSAMMLUNG"
        pdf_doc_title = "Gedankensammlung"
        betreff = "Gedankensammlung"
    elif mode == "signed" and isinstance(seq, int) and seq > 0:
        doc_title = f"BEGEHUNGSPROTOKOLL Nr. {seq}"
        pdf_doc_title = "Baustellenprotokoll"
        betreff = proj if proj != "—" else doc_title
    else:
        doc_title = "SCHNELLNOTIZ"
        pdf_doc_title = "Baustellenprotokoll"
        betreff = proj if proj != "—" else "Schnellnotiz"

    body_text = protocol_display_text(protocol)
    doc_tpl = _new_doc(buf, pdf_doc_title)

    story: list[Any] = []
    story.append(_betreff_datum_block(styles, betreff=betreff, datum=datum, width=doc_tpl.width))
    story.append(Spacer(1, 10))
    story.append(Paragraph(doc_title, styles["title"]))
    story.append(Spacer(1, 4))

    if mode == "thoughts":
        meta_rows = [
            [Paragraph("Bezug", styles["label"]), Paragraph("Ohne Baustelle", styles["value"])],
            [Paragraph("Datum", styles["label"]), Paragraph(_xml_para_text(datum), styles["value"])],
        ]
        section_label = "Gedanken"
    else:
        meta_rows = [
            [Paragraph("Baustelle", styles["label"]), Paragraph(_xml_para_text(proj), styles["value"])],
            [Paragraph("Kunde", styles["label"]), Paragraph(_xml_para_text(customer), styles["value"])],
            [Paragraph("Datum", styles["label"]), Paragraph(_xml_para_text(datum), styles["value"])],
        ]
        if participants:
            meta_rows.append(
                [Paragraph("Teilnehmer", styles["label"]), Paragraph(_xml_para_text(participants), styles["value"])]
            )
        section_label = "Protokoll"

    story.append(_meta_table(meta_rows, doc_tpl.width))
    story.append(Spacer(1, 10))
    story.append(Paragraph(_xml_para_text(section_label), styles["section"]))
    proto_body = ParagraphStyle(
        name="KodraProtoBody",
        parent=styles["body"],
        fontSize=10,
        leading=14,
        spaceAfter=8,
    )
    for para in _protocol_body_paragraphs(body_text):
        story.append(Paragraph(_xml_para_text(para), proto_body))

    _append_pdf_signatures(
        story,
        doc_tpl,
        protocol_for_pdf_signatures(protocol, company_profile),
        section_head=styles["section"],
        info_label_style=styles["label"],
        meta_style=styles["meta"],
        resolve_signature=resolve_signature,
        signature_customer_label="Unternehmer",
        signature_employee_label="Gesprächspartner",
    )
    return _finalize(buf, doc_tpl, story)


def build_kodra_collective_protocol_pdf_bytes(
    payload: dict[str, Any],
    company_profile: dict[str, Any],
    *,
    resolve_logo: Any = None,
    resolve_signature: Any = None,
) -> bytes:
    """Gesamtprotokoll im Kodra-Rahmen."""
    _ = (resolve_logo, resolve_signature, company_profile)
    buf = BytesIO()
    doc_tpl = _new_doc(buf, "Gesamtprotokoll")
    styles = _styles()
    proj = str(payload.get("projectName") or "—")
    customer = str(payload.get("customerName") or "—")
    rng = str(payload.get("sequenceRange") or "—")
    date_range = str(payload.get("dateRange") or "—")
    # dateRange kann bereits „TT.MM.JJJJ – …“ sein
    datum_label = date_range if date_range != "—" else _format_date_de(str(payload.get("dateTo") or ""))

    story: list[Any] = []
    story.append(_betreff_datum_block(styles, betreff=proj, datum=datum_label, width=doc_tpl.width))
    story.append(Spacer(1, 10))
    story.append(Paragraph("GESAMTPROTOKOLL", styles["title"]))
    story.append(Spacer(1, 4))
    meta_rows = [
        [Paragraph("Baustelle", styles["label"]), Paragraph(_xml_para_text(proj), styles["value"])],
        [Paragraph("Kunde", styles["label"]), Paragraph(_xml_para_text(customer), styles["value"])],
        [Paragraph("Nummern", styles["label"]), Paragraph(_xml_para_text(rng), styles["value"])],
        [Paragraph("Zeitraum", styles["label"]), Paragraph(_xml_para_text(date_range), styles["value"])],
        [
            Paragraph("Begehungen", styles["label"]),
            Paragraph(_xml_para_text(str(payload.get("visitCount") or 0)), styles["value"]),
        ],
    ]
    story.append(_meta_table(meta_rows, doc_tpl.width))
    story.append(Spacer(1, 10))

    entries = payload.get("entries") or []
    if isinstance(entries, list) and entries:
        for ent in entries:
            if not isinstance(ent, dict):
                continue
            seq = ent.get("sequenceNumber")
            day = _format_date_de(str(ent.get("date") or "—"))
            head = f"Begehung Nr. {seq}" if isinstance(seq, int) and seq > 0 else "Begehung"
            head = f"{head} · {day}"
            parts = str(ent.get("participants") or "").strip()
            if parts:
                head = f"{head} · {parts}"
            story.append(Paragraph(_xml_para_text(head), styles["section"]))
            text = str(ent.get("text") or "").strip() or "Keine Angabe"
            for para in _protocol_body_paragraphs(text):
                story.append(Paragraph(_xml_para_text(para), styles["section_text"]))
    else:
        story.append(Paragraph("Keine Begehungsprotokolle vorhanden.", styles["section_text"]))

    return _finalize(buf, doc_tpl, story)
