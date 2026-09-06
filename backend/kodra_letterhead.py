"""Briefpapier-Layout nur für L.Kodra Stuckateurhandwerk (Pilot-Tenant).

Andere Mandanten werden hier nicht angefasst — Aufruf nur nach Tenant-Check.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

# Owner = Tenant (Admin-Karte L.Kodra Stuckateurhandwerk)
KODRA_TENANT_ID = "a1100a06-fd44-4020-8321-20b08856a55b"

KODRA_ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "kodra"
KODRA_LOGO_PATH = KODRA_ASSETS_DIR / "logo.png"

KODRA_NAVY = HexColor("#1B3A6B")
KODRA_FOOTER = HexColor("#4A4A4A")
KODRA_TEAL = HexColor("#00FFBF")
KODRA_GREY = HexColor("#2C2C2C")

# Statische Briefkopf-Daten wie in der Kunden-PDF
KODRA_COMPANY = "L.Kodra Stuckateurhandwerk"
KODRA_STREET = "Oberglösinger Straße 30"
KODRA_CITY = "59823 Arnsberg"
KODRA_WEB = "www.verputzer-sauerland.de"
KODRA_PHONE = "+49 171 5166805"
KODRA_EMAIL = "info@l-kodra.de"
KODRA_CONTACT = "Erion Kodra"
KODRA_WINDOW_LINE = f"{KODRA_COMPANY} | {KODRA_STREET} | {KODRA_CITY}"

KODRA_FOOTER_GF = "Geschäftsführer\nErion Kodra"
KODRA_FOOTER_TAX = "USt-ID: DE 417747342\nSteuernummer: 303/5060/2367\nAmtsgericht Arnsberg"
KODRA_FOOTER_BANK = (
    "Volksbank Sauerland eG\n"
    "Inhaber: Lulzim Kodra\n"
    "IBAN: DE80 4606 2817 3614 9350 00\n"
    "BIC: GENODEM1SMA"
)

# Ränder für Flowables (Briefkopf + Fußzeile freilassen)
# Top bewusst so, dass unter der Fensterzeile Platz für Empfängeranschrift ist.
KODRA_LEFT_MARGIN = 2.5 * cm
KODRA_RIGHT_MARGIN = 2.0 * cm
KODRA_TOP_MARGIN = 5.85 * cm
KODRA_BOTTOM_MARGIN = 3.4 * cm


def recipient_address_lines(doc: dict[str, Any] | None) -> list[str]:
    """Kunden-Briefanschrift: Name, Straße, PLZ/Ort (leer = nichts anzeigen)."""
    if not isinstance(doc, dict):
        return []
    name = str(doc.get("customerName") or "").strip()
    address = str(doc.get("projectAddress") or doc.get("address") or "").strip()
    city = str(doc.get("projectCity") or doc.get("city") or "").strip()
    return [line for line in (name, address, city) if line]


def is_kodra_export(doc: dict[str, Any] | None, company_profile: dict[str, Any] | None = None) -> bool:
    """True nur für den Kodra-Mandanten (ID oder eindeutiger Firmenname)."""
    for src in (doc, company_profile):
        if not isinstance(src, dict):
            continue
        tid = str(src.get("companyId") or src.get("tenantId") or "").strip()
        if tid == KODRA_TENANT_ID:
            return True
    name = ""
    if isinstance(doc, dict):
        name = str(doc.get("companyName") or "")
    if not name and isinstance(company_profile, dict):
        name = str(company_profile.get("companyName") or "")
    n = name.casefold()
    return "kodra" in n and "stuckateur" in n


def _draw_multiline(
    canv: Canvas,
    text: str,
    x: float,
    y: float,
    *,
    font: str = "Helvetica",
    size: float = 7,
    leading: float = 9,
    fill=KODRA_FOOTER,
) -> None:
    canv.setFillColor(fill)
    canv.setFont(font, size)
    for i, line in enumerate(text.split("\n")):
        canv.drawString(x, y - i * leading, line)


def _draw_corner_vector(canv: Canvas, page_h: float) -> None:
    """Eck-Grafik oben links (Türkis + Grau) — wie Kunden-Briefpapier."""
    y_top = page_h
    # Türkis-Keil
    canv.setFillColor(KODRA_TEAL)
    p = canv.beginPath()
    p.moveTo(0, y_top)
    p.lineTo(1.85 * cm, y_top)
    p.lineTo(0.72 * cm, y_top - 0.95 * cm)
    p.lineTo(0, y_top - 1.25 * cm)
    p.close()
    canv.drawPath(p, fill=1, stroke=0)
    # Grauer Keil (weiße Lücke dazwischen)
    canv.setFillColor(KODRA_GREY)
    p2 = canv.beginPath()
    p2.moveTo(2.05 * cm, y_top)
    p2.lineTo(4.85 * cm, y_top)
    p2.lineTo(3.15 * cm, y_top - 0.95 * cm)
    p2.lineTo(0.92 * cm, y_top - 0.95 * cm)
    p2.close()
    canv.drawPath(p2, fill=1, stroke=0)


def draw_kodra_letterhead(canv: Canvas, doc: Any) -> None:
    """Kopf + Fuß auf jeder Seite (1:1 an Kunden-PDF angelehnt)."""
    page_w, page_h = A4
    page_num = int(getattr(doc, "page", 1) or 1)
    page_count = int(getattr(doc, "page_count", 0) or 0)

    canv.saveState()

    # --- Kopf: Ecke (vektor, kein gestrecktes PNG) ---
    _draw_corner_vector(canv, page_h)

    # --- Kopf: Logo rechts ---
    logo_w = 5.5 * cm
    logo_h = 2.15 * cm
    logo_x = page_w - KODRA_RIGHT_MARGIN - logo_w
    logo_y = page_h - 1.0 * cm - logo_h
    if KODRA_LOGO_PATH.is_file():
        try:
            canv.drawImage(
                str(KODRA_LOGO_PATH),
                logo_x,
                logo_y,
                width=logo_w,
                height=logo_h,
                mask="auto",
                preserveAspectRatio=True,
            )
        except Exception:
            canv.setFillColor(KODRA_NAVY)
            canv.setFont("Helvetica-Bold", 14)
            canv.drawRightString(page_w - KODRA_RIGHT_MARGIN, page_h - 1.6 * cm, "L. Kodra")

    # --- Kopf: Kontaktdaten unter Logo ---
    contact_x = logo_x
    contact_top = logo_y - 0.25 * cm
    canv.setFillColor(KODRA_NAVY)
    canv.setFont("Helvetica-Bold", 8)
    canv.drawString(contact_x, contact_top, KODRA_COMPANY)
    canv.setFont("Helvetica", 7.5)
    canv.setFillColor(KODRA_FOOTER)
    lines = [
        KODRA_STREET,
        KODRA_CITY,
        KODRA_WEB,
        f"Telefon  {KODRA_PHONE}",
        f"E-Mail  {KODRA_EMAIL}",
    ]
    y = contact_top - 0.32 * cm
    for line in lines:
        canv.drawString(contact_x, y, line)
        y -= 0.28 * cm
    canv.setFont("Helvetica-Bold", 7.5)
    canv.setFillColor(KODRA_NAVY)
    canv.drawString(contact_x, y - 0.08 * cm, "Ansprechperson")
    canv.setFont("Helvetica", 7.5)
    canv.setFillColor(KODRA_FOOTER)
    canv.drawString(contact_x + 2.6 * cm, y - 0.08 * cm, KODRA_CONTACT)

    # --- Fensterzeile (links) ---
    canv.setFillColor(KODRA_FOOTER)
    canv.setFont("Helvetica", 6.5)
    canv.drawString(KODRA_LEFT_MARGIN, page_h - 5.55 * cm, KODRA_WINDOW_LINE)

    # --- Fußzeile ---
    foot_y = 2.15 * cm
    col1 = KODRA_LEFT_MARGIN
    col2 = 5.5 * cm
    col3 = 10.5 * cm
    _draw_multiline(canv, KODRA_FOOTER_GF, col1, foot_y, size=6.5, leading=8)
    _draw_multiline(canv, KODRA_FOOTER_TAX, col2, foot_y, size=6.5, leading=8)
    _draw_multiline(canv, KODRA_FOOTER_BANK, col3, foot_y, size=6.5, leading=8)
    canv.setFillColor(KODRA_FOOTER)
    canv.setFont("Helvetica", 6.5)
    if page_count > 0:
        canv.drawRightString(page_w - KODRA_RIGHT_MARGIN, foot_y, f"Seite {page_num} von {page_count}")
    else:
        canv.drawRightString(page_w - KODRA_RIGHT_MARGIN, foot_y, f"Seite {page_num}")

    # dünne Trennlinie über Fuß
    canv.setStrokeColor(HexColor("#D4D4D8"))
    canv.setLineWidth(0.4)
    canv.line(KODRA_LEFT_MARGIN, 2.85 * cm, page_w - KODRA_RIGHT_MARGIN, 2.85 * cm)

    canv.restoreState()
