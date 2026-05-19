"""
Optionale OpenAI-Strukturierung für Tagesberichte.

Ohne gültiges OPENAI_API_KEY liefert structure_report_with_ai None — Fallback bleibt lokal (report_structure).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

_logger = logging.getLogger(__name__)

JSON_SCHEMA_KEYS = frozenset(
    {"summary", "activities", "materials", "problems", "openItems", "customerTalk"}
)

SYSTEM_PROMPT = """Du bist ein professioneller Bau-/Handwerks-Dokumentationsassistent.
Du strukturierst frei gesprochene oder getippte Tagesberichte in saubere Baustellenberichte.
Du erfindest keine Fakten und ergänzend keine Arbeiten, Materialien oder Zitate, die nicht im Rohtext oder in den angegeben Formularfeldern vorkommen.
Wenn eine Kategorie keine belastbare Information enthält: setze Liste auf [] oder customerTalk/summary auf "Keine Angabe" wo sinnvoll.
Tätigkeiten = konkret ausgeführte Arbeiten / Handlungen auf der Baustelle.
Material = Baustoffe, Werkzeuge, Bauteile, Lieferungen (rein benennend, keine erfundenen Mengen ohne Textgrundlage).
Probleme = Störungen, Verzögerungen, konkret fehlendes/defektes.
Offene Punkte = noch zu erledigen, Nachliefern, Klärungen, Termine.
Kundengespräch = relevante Kommunikation mit Kunde/Bauherr/Auftraggeber nur wenn im Kontext erwähnt.
Überführe Umgangssprache in professionelles Baustellen-Deutsch.
Nutze Fachsprache und korrigiere Rechtschreibung.
Normalisiere Mengen/Einheiten, falls im Text ableitbar (z. B. qm -> m², kubikmeter -> m³), aber ohne Fakten zu erfinden.
Trenne Tätigkeiten und Material sauber.
Wenn Tätigkeiten vorhanden sind, erzeuge immer eine sinnvolle Zusammenfassung.
Formuliere Kundengespräch professionell.
Kopiere den Rohtext nicht unverändert in mehrere Felder.
Vermeide Umgangssprache wie "reingemacht", "fertig gemacht", "dran gemacht".
Bevorzuge professionelles, natürliches Business-Deutsch für das Handwerk.
Berücksichtige branchenspezifische Begriffe aus GaLaBau, SHK, Trockenbau, Fliesen, Elektro, Sanierung, Hoch-/Tiefbau und Dacharbeiten.

Antworte ausschließlich als ein gültiges JSON-Objekt mit genau diesen Schlüsseln (englische Schlüssel, Werte deutsch):
{"summary":"","activities":[],"materials":[],"problems":[],"openItems":[],"customerTalk":""}

Keine Codeblöcke, keine Erklärung außerhalb des JSON."""

USER_TEMPLATE = """Strukturiere den folgenden Tagesbericht.

Firma (laut Stammdaten): {company_name}
Baustelle: {project_name}
Kunde: {customer_name}
Datum: {date}
Ausgewählte Mitarbeiter: {employees}
Arbeitszeit aus Formular (Start–Ende): {start_time} – {end_time}

Rohtext:
{raw_text}
"""


def structure_report_with_ai(input_data: dict[str, Any]) -> dict[str, Any] | None:
    """
    Versucht strukturierte Felder über OpenAI zu erzeugen.

    Ruft keine API auf, wenn OPENAI_API_KEY fehlt oder leer ist.
    Bei Parsing-/API-/Validierungsfehler: wird None zurückgegeben (keine Tracebacks nach außen).

    Gibt bei Erfolg ein dict nur mit Schema-Schlüsseln (camelCase laut Frontend) zurück.
    """
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        return None

    model = (os.environ.get("OPENAI_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"

    raw_text = str(input_data.get("rawText") or input_data.get("raw_text") or "").strip()

    body = USER_TEMPLATE.format(
        company_name=str(input_data.get("companyName") or input_data.get("company_name") or "").strip()
        or "Keine Angabe",
        project_name=str(input_data.get("projectName") or input_data.get("project_name") or "").strip()
        or "Keine Angabe",
        customer_name=str(input_data.get("customerName") or input_data.get("customer_name") or "").strip()
        or "Keine Angabe",
        date=str(input_data.get("date") or "").strip() or "Keine Angabe",
        employees=_fmt_employees(input_data.get("employeeNames") or input_data.get("employee_names")),
        start_time=str(input_data.get("startTime") or input_data.get("start_time") or "").strip()
        or "Keine Angabe",
        end_time=str(input_data.get("endTime") or input_data.get("end_time") or "").strip() or "Keine Angabe",
        raw_text=raw_text if raw_text else "(leer)",
    )

    try:
        from openai import OpenAI  # Lazy import wenn Key gesetzt ist

        client = OpenAI(api_key=key)
        completion = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": body},
            ],
            response_format={"type": "json_object"},
        )
        content = (completion.choices[0].message.content or "").strip()
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            return None
        normalized = _normalize_ai_structure(parsed)
        if normalized is None:
            _logger.warning("AI structure failed, using local fallback")
            return None
        return normalized
    except Exception:
        _logger.warning("AI structure failed, using local fallback")
        return None


def _fmt_employees(val: Any) -> str:
    if isinstance(val, list) and val:
        return ", ".join(str(x).strip() for x in val if str(x).strip()) or "Keine Angabe"
    return "Keine Angabe"


def _as_str_list(v: Any, *, max_items: int = 80) -> list[str]:
    if v is None:
        return []
    if not isinstance(v, list):
        return []
    out: list[str] = []
    for item in v[:max_items]:
        s = str(item).strip() if item is not None else ""
        if s:
            out.append(s)
    return out


def _as_str_scalar(v: Any, default: str = "Keine Angabe") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def _normalize_ai_structure(parsed: dict[str, Any]) -> dict[str, Any] | None:
    """Normalisiert Modell-Antwort zu exakt einem sechsstufigen Zielschema (camelCase)."""
    open_raw = parsed.get("openItems")
    if open_raw is None and "open_items" in parsed:
        open_raw = parsed.get("open_items")

    cust = parsed.get("customerTalk")
    if cust is None and "customer_talk" in parsed:
        cust = parsed.get("customer_talk")

    result = {
        "summary": _as_str_scalar(parsed.get("summary")),
        "activities": _as_str_list(parsed.get("activities")),
        "materials": _as_str_list(parsed.get("materials")),
        "problems": _as_str_list(parsed.get("problems")),
        "openItems": _as_str_list(open_raw),
        "customerTalk": _as_str_scalar(cust),
    }
    return result
