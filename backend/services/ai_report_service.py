"""
Optionale OpenAI-Strukturierung für Tagesberichte.

Ohne gültiges OPENAI_API_KEY liefert structure_report_with_ai None — Fallback bleibt lokal (report_structure).
"""

from __future__ import annotations

import json
import logging
import os
import re
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


SUMMARY_POLISH_SYSTEM = """Du bist ein Bau-/Handwerks-Dokumentationsassistent.
Du formulierst aus einer Liste BEREITS GEPRUEFTER Taetigkeiten
eine natuerliche, professionelle Zusammenfassung fuer einen Bau-Tagesbericht in deutscher Sprache.

STRIKTE REGELN:
- Verwende ausschliesslich die unten aufgefuehrten Taetigkeiten.
- Erfinde NICHTS: keine zusaetzlichen Arbeiten, Materialien, Mengen oder Zahlen.
- Veraendere keine Zahlen, Mengen oder Einheiten.
- Nenne KEINE Materialien, Baustoffe oder Werkzeuge in der Zusammenfassung
  (kein „zum Einsatz“, kein „dafuer kamen“, keine Materialnamen) — Material steht im eigenen Reiter.
- Schreibe 1-3 zusammenhaengende Saetze als Fliesstext (keine Aufzaehlung, keine Stichpunkte).
- Sachlich, klar, freundlich-professionell, natuerliches Business-Deutsch.
- Antworte NUR mit dem Zusammenfassungstext, ohne Anfuehrungszeichen, ohne Vorrede, ohne JSON."""


def polish_summary_with_ai(structured: dict[str, Any], meta: dict[str, Any] | None = None) -> str | None:
    """Hebel 1: formuliert die Zusammenfassung natuerlicher — AUSSCHLIESSLICH aus den
    bereits deterministisch geprueften Daten.

    Sicherheits-Invarianten (rein additiv):
    - Ohne OPENAI_API_KEY oder ohne Taetigkeiten -> None (Aufrufer behaelt die
      deterministische Zusammenfassung).
    - Bei API-/Parsing-/Validierungsfehler -> None (kein Traceback nach aussen).
    - Zahlen-Waechter: enthaelt der KI-Text eine Zahl, die nicht in den geprueften
      Daten vorkommt, wird verworfen -> None. Verhindert erfundene Mengen.
    """
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        return None

    activities = [str(a).strip() for a in (structured.get("activities") or []) if str(a).strip()]
    if not activities:
        return None
    materials = [str(m).strip() for m in (structured.get("materials") or []) if str(m).strip()]
    deterministic = str(structured.get("summary") or "")
    meta = meta or {}

    model = (os.environ.get("OPENAI_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"

    user = (
        f"Datum: {str(meta.get('date') or '').strip() or 'Keine Angabe'}\n"
        f"Baustelle: {str(meta.get('projectName') or '').strip() or 'Keine Angabe'}\n\n"
        "Taetigkeiten (nur diese in der Zusammenfassung verwenden — Materialien weglassen):\n"
        + "\n".join(f"- {a}" for a in activities[:40])
    )

    try:
        from openai import OpenAI  # Lazy import wenn Key gesetzt ist

        client = OpenAI(api_key=key)
        completion = client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": SUMMARY_POLISH_SYSTEM},
                {"role": "user", "content": user},
            ],
        )
        text = (completion.choices[0].message.content or "").strip()
        text = text.strip().strip('"').strip("`").strip()
        from app.services.summary_material_guard import (
            strip_material_echo_from_summary,
            summary_has_material_echo,
        )

        text = strip_material_echo_from_summary(text, materials, activities)
        # Auch die der KI mitgegebenen Meta-Daten (Datum/Baustelle) zaehlen als
        # erlaubte Zahlenquelle – z. B. Hausnummern im Projektnamen.
        meta_src = f"{meta.get('date') or ''} {meta.get('projectName') or ''}"
        if summary_has_material_echo(text, materials, activities):
            _logger.warning("AI summary polish rejected: material echo in summary")
            return None
        if not _polished_summary_is_safe(text, activities, materials, deterministic, meta_src):
            _logger.warning("AI summary polish rejected by guard, using deterministic summary")
            return None
        return text
    except Exception:
        _logger.warning("AI summary polish failed, using deterministic summary")
        return None


CUSTOMER_TALK_POLISH_SYSTEM = """Du bist ein Bau-/Handwerks-Dokumentationsassistent.
Du formulierst aus einem BEREITS ISOLIERTEN Kundengespraech-Text
einen natuerlichen, professionellen Satz oder zwei fuer einen Bau-Tagesbericht in deutscher Sprache.

STRIKTE REGELN:
- Verwende ausschliesslich die unten stehenden Inhalte.
- Erfinde NICHTS: keine zusaetzlichen Details, Termine, Namen, Arbeiten, Materialien oder Mengen.
- Maximal 1-2 kurze Saetze als Fliesstext (keine Aufzaehlung, kein JSON).
- Sachlich, klar, freundlich-professionell — nicht uebertrieben oder werblich.
- Keine Baustellen-Taetigkeiten und keine Materialien erwaehnen.
- Antworte NUR mit dem Kundengespraech-Text, ohne Anfuehrungszeichen, ohne Vorrede."""


def polish_customer_talk_with_ai(
    structured: dict[str, Any],
    *,
    raw_text: str = "",
) -> str | None:
    """Hebel 3: Kundengespraech natuerlicher formulieren — nur aus isoliertem Inhalt.

    Sicherheits-Invarianten (rein additiv):
    - Ohne OPENAI_API_KEY oder ohne belastbares Kundengespraech -> None.
    - Bei API-/Parsing-/Validierungsfehler -> None.
    - Guard verwirft Arbeitstext, neue Zahlen oder verlorene Kunden-Fakten.
    """
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        return None

    deterministic = str(structured.get("customerTalk") or "").strip()
    if not deterministic or deterministic.casefold() == "keine angabe":
        return None

    model = (os.environ.get("OPENAI_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"
    user = (
        "Isoliertes Kundengespraech (nur daraus formulieren, nichts hinzufuegen):\n"
        f"{deterministic}"
    )

    try:
        from openai import OpenAI  # Lazy import wenn Key gesetzt ist
        from app.services.customer_talk_guard import (
            customer_talk_polish_is_safe,
            strip_work_pollution_from_customer_talk,
        )

        client = OpenAI(api_key=key)
        completion = client.chat.completions.create(
            model=model,
            temperature=0.25,
            messages=[
                {"role": "system", "content": CUSTOMER_TALK_POLISH_SYSTEM},
                {"role": "user", "content": user},
            ],
        )
        text = (completion.choices[0].message.content or "").strip()
        text = text.strip().strip('"').strip("`").strip()
        text = strip_work_pollution_from_customer_talk(text)
        if not text:
            return None
        summary = str(structured.get("summary") or "")
        if not customer_talk_polish_is_safe(
            text,
            deterministic,
            raw_text=raw_text,
            summary=summary,
        ):
            _logger.warning("AI customer talk polish rejected by guard, using deterministic text")
            return None
        return text
    except Exception:
        _logger.warning("AI customer talk polish failed, using deterministic customer talk")
        return None


PROBLEM_ITEM_POLISH_SYSTEM = """Du bist ein Bau-/Handwerks-Dokumentationsassistent.
Du formulierst BEREITS ISOLIERTE Baustellen-Probleme als kurze, professionelle Saetze.

STRIKTE REGELN:
- Verwende ausschliesslich die unten gelieferten Problem-Inhalte.
- Erfinde NICHTS: keine zusaetzlichen Stoerungen, Arbeiten, Materialien oder Mengen.
- Pro Eintrag maximal 1 kurzer Satz.
- Keine Taetigkeiten, kein Kundengespraech, keine offenen Punkte.
- Antworte als JSON-Objekt: {"items":["..."]} mit exakt gleicher Anzahl wie die Eingabe."""


OPEN_ITEM_POLISH_SYSTEM = """Du bist ein Bau-/Handwerks-Dokumentationsassistent.
Du formulierst BEREITS ISOLIERTE offene Punkte als kurze, professionelle Saetze.

STRIKTE REGELN:
- Verwende ausschliesslich die unten gelieferten offenen Punkte.
- Erfinde NICHTS: keine zusaetzlichen Aufgaben, Termine, Arbeiten oder Mengen.
- Pro Eintrag maximal 1 kurzer Satz; der Punkt soll klar als offen erkennbar bleiben.
- Keine Taetigkeiten, kein Kundengespraech, keine Probleme.
- Antworte als JSON-Objekt: {"items":["..."]} mit exakt gleicher Anzahl wie die Eingabe."""


def _polish_string_list_with_ai(
    items: list[str],
    *,
    system_prompt: str,
    guard_fn: Any,
    raw_text: str,
    log_label: str,
) -> list[str] | None:
    vals = [str(x).strip() for x in items if str(x).strip()]
    if not vals:
        return None

    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        return None

    model = (os.environ.get("OPENAI_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"
    user = json.dumps({"items": vals}, ensure_ascii=False)

    try:
        from openai import OpenAI  # Lazy import wenn Key gesetzt ist
        from app.services.problem_open_guard import strip_pollution_from_problem_open_item

        client = OpenAI(api_key=key)
        completion = client.chat.completions.create(
            model=model,
            temperature=0.25,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
        )
        content = (completion.choices[0].message.content or "").strip()
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            return None
        out_raw = parsed.get("items")
        if not isinstance(out_raw, list) or len(out_raw) != len(vals):
            return None

        out: list[str] = []
        for det, polished in zip(vals, out_raw):
            text = strip_pollution_from_problem_open_item(str(polished or "").strip())
            if not text:
                return None
            if not guard_fn(text, det, raw_text=raw_text):
                _logger.warning("AI %s polish rejected by guard: %r", log_label, text)
                return None
            out.append(text)
        return out
    except Exception:
        _logger.warning("AI %s polish failed, using deterministic list", log_label)
        return None


def polish_problems_with_ai(
    structured: dict[str, Any],
    *,
    raw_text: str = "",
) -> list[str] | None:
    from app.services.problem_open_guard import problem_item_polish_is_safe

    items = [str(x).strip() for x in (structured.get("problems") or []) if str(x).strip()]
    return _polish_string_list_with_ai(
        items,
        system_prompt=PROBLEM_ITEM_POLISH_SYSTEM,
        guard_fn=problem_item_polish_is_safe,
        raw_text=raw_text,
        log_label="problem",
    )


def polish_open_items_with_ai(
    structured: dict[str, Any],
    *,
    raw_text: str = "",
) -> list[str] | None:
    from app.services.problem_open_guard import open_item_polish_is_safe

    items = [str(x).strip() for x in (structured.get("openItems") or []) if str(x).strip()]
    return _polish_string_list_with_ai(
        items,
        system_prompt=OPEN_ITEM_POLISH_SYSTEM,
        guard_fn=open_item_polish_is_safe,
        raw_text=raw_text,
        log_label="open item",
    )


def polish_problem_open_with_ai(
    structured: dict[str, Any],
    *,
    raw_text: str = "",
) -> dict[str, list[str]] | None:
    """Hebel 4: Probleme und offene Punkte natuerlicher formulieren."""
    problems = polish_problems_with_ai(structured, raw_text=raw_text)
    opens = polish_open_items_with_ai(structured, raw_text=raw_text)
    if problems is None and opens is None:
        return None
    result: dict[str, list[str]] = {}
    if problems is not None:
        result["problems"] = problems
    if opens is not None:
        result["openItems"] = opens
    return result or None


COLLECTIVE_SUMMARY_SYSTEM = """Du bist ein Bau-/Handwerks-Dokumentationsassistent.
Du fasst mehrere BEREITS GEPRUEFTE Tagesberichte EINER Baustelle zu einer einzigen,
natuerlichen Gesamt-Zusammenfassung zusammen (deutscher Fliesstext).

STRIKTE REGELN:
- Verwende ausschliesslich die unten gelieferten Inhalte (Zeitraum, Stunden, Taetigkeiten je Tag, Besonderheiten, Materialien).
- Erfinde NICHTS und veraendere keine Zahlen, Mengen, Einheiten oder Daten.
- Beschreibe den Fortschritt/Verlauf ueber die Tage hinweg (nicht nur einen Tag).
- Nenne den Zeitraum und die Gesamtstunden, sofern angegeben.
- 2 bis 5 zusammenhaengende Saetze als Fliesstext (keine Aufzaehlung, keine Stichpunkte, kein JSON).
- Sachlich, klar, professionell, natuerliches Business-Deutsch.
- Antworte NUR mit dem Zusammenfassungstext, ohne Anfuehrungszeichen, ohne Vorrede."""


def polish_collective_summary_with_ai(
    payload: dict[str, Any], deterministic: str
) -> str | None:
    """Formuliert die GESAMT-Zusammenfassung eines Durchlaufs natuerlich — kombiniert
    ueber alle Tage, ausschliesslich aus den bereits geprueften Tagesbericht-Daten.

    Sicherheits-Invarianten (rein additiv, wie polish_summary_with_ai):
    - Ohne OPENAI_API_KEY oder ohne Tage/Taetigkeiten -> None (Aufrufer behaelt die
      deterministische Gesamt-Zusammenfassung).
    - Bei API-/Parsing-/Validierungsfehler -> None.
    - Zahlen-Waechter: jede Zahl im KI-Text muss aus den geprueften Daten stammen.
    """
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        return None

    days = [d for d in (payload.get("days") or []) if isinstance(d, dict)]
    if not days:
        return None

    totals = payload.get("totals") if isinstance(payload.get("totals"), dict) else {}
    materials = [str(m).strip() for m in (totals.get("materials") or []) if str(m).strip()]

    # Erlaubte Zahlenquellen + Tagesinhalte fuer den Prompt sammeln.
    day_blocks: list[str] = []
    allowed_src_parts: list[str] = [deterministic, str(payload.get("dateFrom") or ""), str(payload.get("dateTo") or "")]
    allowed_src_parts.append(str(totals.get("totalHours") or ""))
    allowed_src_parts.append(str(totals.get("reportCount") or ""))
    allowed_src_parts.append(str(len(days)))
    for d in days:
        acts = [str(a).strip() for a in (d.get("activities") or []) if str(a).strip()]
        note = str(d.get("notes") or "").strip()
        emps = [str(e).strip() for e in (d.get("employees") or []) if str(e).strip()]
        date_lbl = str(d.get("date") or "").strip() or "Keine Angabe"
        block = f"Tag {date_lbl} ({_fmt_hours_value(d.get('hours'))} h, {', '.join(emps) or 'keine Angabe'}):"
        if acts:
            block += "\n  Taetigkeiten: " + "; ".join(acts[:12])
        if note:
            block += "\n  Besonderheiten: " + note
        day_blocks.append(block)
        allowed_src_parts.extend(acts)
        allowed_src_parts.append(note)
        allowed_src_parts.append(str(d.get("hours") or ""))
        allowed_src_parts.extend(emps)
    for row in (totals.get("hoursByEmployee") or []):
        if isinstance(row, dict):
            allowed_src_parts.append(str(row.get("hours") or ""))

    model = (os.environ.get("OPENAI_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"

    user = (
        f"Baustelle: {str(payload.get('projectName') or '').strip() or 'Keine Angabe'}\n"
        f"Zeitraum: {str(payload.get('dateFrom') or '—')} bis {str(payload.get('dateTo') or '—')}\n"
        f"Arbeitstage: {len(days)}\n"
        f"Gesamtstunden: {_fmt_hours_value(totals.get('totalHours'))}\n\n"
        "Tagesberichte:\n" + "\n".join(day_blocks[:60])
    )
    if materials:
        user += "\n\nMaterialien (gesamt):\n" + "\n".join(f"- {m}" for m in materials[:40])

    try:
        from openai import OpenAI  # Lazy import wenn Key gesetzt ist

        client = OpenAI(api_key=key)
        completion = client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": COLLECTIVE_SUMMARY_SYSTEM},
                {"role": "user", "content": user},
            ],
        )
        text = (completion.choices[0].message.content or "").strip()
        text = text.strip().strip('"').strip("`").strip()
        if not _collective_summary_is_safe(text, " ".join(allowed_src_parts)):
            _logger.warning("AI collective summary rejected by guard, using deterministic summary")
            return None
        return text
    except Exception:
        _logger.warning("AI collective summary failed, using deterministic summary")
        return None


def _fmt_hours_value(value: Any) -> str:
    try:
        return f"{float(value):.2f}".replace(".", ",")
    except Exception:
        return "0,00"


def _collective_summary_is_safe(text: str, allowed_src: str) -> bool:
    t = str(text or "").strip()
    if len(t) < 10 or len(t) > 1500:
        return False
    if "{" in t or "}" in t or "[" in t:
        return False
    allowed = set(re.findall(r"\d+", allowed_src))
    found = set(re.findall(r"\d+", t))
    if found - allowed:
        return False
    return True


def _polished_summary_is_safe(
    text: str,
    activities: list[str],
    materials: list[str],
    deterministic: str,
    extra_allowed: str = "",
) -> bool:
    t = str(text or "").strip()
    if len(t) < 10 or len(t) > 800:
        return False
    if "{" in t or "}" in t or "[" in t:  # keine JSON-/Listen-Artefakte
        return False
    # Zahlen-Waechter: jede Zahl im KI-Text muss in den geprueften Daten (inkl.
    # mitgegebener Meta-Daten wie Datum/Baustelle) vorkommen.
    allowed = set(
        re.findall(r"\d+", " ".join([deterministic, extra_allowed, *activities, *materials]))
    )
    found = set(re.findall(r"\d+", t))
    if found - allowed:
        return False
    try:
        from app.services.summary_material_guard import summary_has_material_echo

        if summary_has_material_echo(t, materials, activities):
            return False
    except Exception:
        pass
    return True


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


PROTOCOL_POLISH_SYSTEM = """Du bist ein Assistent fuer Baustellenprotokolle auf Deutsch.
Du korrigierst NUR Rechtschreibung, Grammatik und Interpunktion eines gesprochenen Textes.
Du setzt sinnvolle Absaetze (Leerzeile) ein, wo der Sprecher thematisch wechselt.

STRIKTE REGELN:
- Aendere NICHT den Inhalt. Keine neuen Fakten, keine Ergaenzungen, keine Zusammenfassung.
- Entferne keine Informationen und keine Aussagen des Sprechers.
- Keine Ueberschriften, keine Aufzaehlungszeichen, kein JSON.
- Behalte die Wortwahl des Sprechers so nah wie moeglich bei.
- Antworte NUR mit dem bereinigten Fliesstext, ohne Anfuehrungszeichen, ohne Vorrede."""


def polish_protocol_transcript_with_ai(raw_text: str) -> str | None:
    """Leichtes KI-Glaetten fuer Baustellenprotokolle — nur Orthografie/Interpunktion."""
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    raw = str(raw_text or "").strip()
    if not key or len(raw) < 3:
        return None

    model = (os.environ.get("OPENAI_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key)
        completion = client.chat.completions.create(
            model=model,
            temperature=0.1,
            messages=[
                {"role": "system", "content": PROTOCOL_POLISH_SYSTEM},
                {"role": "user", "content": raw},
            ],
        )
        text = (completion.choices[0].message.content or "").strip()
        text = text.strip().strip('"').strip("`").strip()
        if len(text) < max(3, int(len(raw) * 0.5)):
            return None
        return text
    except Exception:
        _logger.warning("AI protocol polish failed, using raw transcript")
        return None
