"""Notiz-Übersetzer — nur Stichpunkte, Sprach-Sätze unberührt.

Wenn der Rohtext wie kurze Notizen ohne Tätigkeitsverb aussieht, werden
Zeilen in Sätze übersetzt, die die bestehende Engine schon versteht.
Gesprochene Sätze mit Verben werden nicht angefasst.
"""

from __future__ import annotations

import re

# Gleiche Idee wie report_structure.ACTIVITY_MARKERS — Guard: Sprache nicht anfassen.
_BLOCKING_VERBS = (
    "gemacht",
    "gebaut",
    "gelegt",
    "gepflastert",
    "vorbereitet",
    "eingebaut",
    "montiert",
    "installiert",
    "angeschlossen",
    "gestrichen",
    "gespachtelt",
    "verlegt",
    "abgerissen",
    "gereinigt",
    "verdichtet",
    "gesetzt",
    "repariert",
    "ausgetauscht",
    "geprüft",
    "geprueft",
    "betoniert",
    "verputzt",
    "gebohrt",
    "demontiert",
    "transportiert",
    "verfugt",
    "ausgeführt",
    "ausgefuehrt",
    "gearbeitet",
    "geschraubt",
    "gemäht",
    "gemaeht",
    "geschnitten",
    "getrimmt",
    "gejätet",
    "gejaetet",
    "gezupft",
    "gefegt",
    "gezogen",
    "ausgehoben",
    "eingesandet",
)

# Bekannte Notiz-Wörter → Standardverb (nur wenn kein Verb in der Zeile steht).
_NOUN_RULES: tuple[tuple[str, str, str], ...] = (
    (r"pflastersteine|pflaster", "verlegt", "Pflaster"),
    (r"kabel", "verlegt", "Kabel"),
    (r"kg[\s-]?rohre?|rohre?", "verlegt", "Rohre"),
    (r"handschachtung|handschaltung|handschacht", "ausgeführt", "Handschachtung"),
    (r"randsteine?", "gesetzt", "Randsteine"),
    (r"schotter", "eingebaut", "Schotter"),
    (r"splitt|split", "eingebaut", "Splitt"),
    (r"vlies", "verlegt", "Vlies"),
    (r"fliesen", "verlegt", "Fliesen"),
    (r"beton", "eingebracht", "Beton"),
)

_QTY = re.compile(
    r"^(?P<qty>\d+(?:[.,]\d+)?)\s*"
    r"(?P<unit>qm|m²|m2|m³|m3|lfm|lfdm|stk|stck|std\.?|stunden?|meter|m|quadratmeter|kubikmeter)\.?\s+"
    r"(?P<rest>.+)$",
    re.IGNORECASE,
)
_HOURS = re.compile(
    r"^(?P<qty>\d+(?:[.,]\d+)?)\s*(?:std\.?|stunden?)\s+(?P<rest>.+)$",
    re.IGNORECASE,
)
_LOC_LABEL = re.compile(
    r"^(laterne|haus|bauteil|abschnitt|hausnr|nr)\s*\d+[a-z]?$",
    re.IGNORECASE,
)


def _has_blocking_verb(text: str) -> bool:
    low = str(text or "").casefold()
    return any(v in low for v in _BLOCKING_VERBS)


def looks_like_notes(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw:
        return False
    if _has_blocking_verb(raw):
        return False
    lines = [ln.strip() for ln in re.split(r"[\n;]+", raw) if ln.strip()]
    if len(lines) >= 2:
        short = sum(1 for ln in lines if len(ln) <= 56)
        return short >= 2 and short >= int(len(lines) * 0.6)
    if len(raw) <= 72 and re.search(r"\d", raw) and re.search(r"[A-Za-zÄÖÜäöüß]{3,}", raw):
        return True
    return False


def _norm_unit(unit: str) -> str:
    u = str(unit or "").strip().casefold().replace(".", "")
    mapping = {
        "qm": "m²",
        "m2": "m²",
        "m²": "m²",
        "quadratmeter": "m²",
        "m3": "m³",
        "m³": "m³",
        "kubikmeter": "m³",
        "lfm": "lfm",
        "lfdm": "lfm",
        "meter": "m",
        "m": "m",
        "stk": "Stk",
        "stck": "Stk",
        "std": "Stunde",
        "stunde": "Stunde",
        "stunden": "Stunden",
    }
    return mapping.get(u, unit.strip())


def _match_noun(rest: str) -> tuple[str, str] | None:
    blob = str(rest or "").strip()
    if not blob:
        return None
    low = blob.casefold()
    for pattern, verb, label in _NOUN_RULES:
        if re.search(rf"\b(?:{pattern})\b", low):
            return label, verb
    return None


def _expand_line(line: str) -> str:
    src = str(line or "").strip(" -•\t")
    if not src:
        return ""
    if _has_blocking_verb(src):
        return src if src.endswith(".") else src + "."
    if _LOC_LABEL.match(src):
        return src if src.endswith(".") else src + "."

    hours = _HOURS.match(src)
    if hours:
        rest = hours.group("rest").strip()
        qty = hours.group("qty").replace(",", ".")
        hit = _match_noun(rest)
        if hit:
            label, verb = hit
            return f"{qty} Stunde {label} {verb}."
        return src if src.endswith(".") else src + "."

    qty_m = _QTY.match(src)
    if qty_m:
        rest = qty_m.group("rest").strip()
        qty = qty_m.group("qty").replace(",", ".")
        unit = _norm_unit(qty_m.group("unit"))
        hit = _match_noun(rest)
        if hit:
            label, verb = hit
            if unit in {"Stunde", "Stunden"}:
                return f"{qty} Stunde {label} {verb}."
            return f"{qty} {unit} {label} {verb}."
        return src if src.endswith(".") else src + "."

    hit = _match_noun(src)
    if hit:
        label, verb = hit
        return f"{label} {verb}."
    return src if src.endswith(".") else src + "."


def expand_notes_if_guarded(raw_text: str) -> str:
    """Unverändert zurück, wenn der Text nicht wie Stichpunkte ohne Verb wirkt."""
    original = str(raw_text or "")
    if not looks_like_notes(original):
        return original
    lines = [ln.strip() for ln in re.split(r"[\n;]+", original) if ln.strip()]
    if not lines:
        return original
    sentences = [_expand_line(ln) for ln in lines]
    sentences = [s for s in sentences if s]
    if not sentences:
        return original
    return " ".join(sentences)
