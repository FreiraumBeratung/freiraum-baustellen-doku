"""Extraktion und Formulierung von Problemen und offenen Punkten aus Rohtext.

Rein additiv: trennt Problem/Offen von Arbeit, Material und Kundengespräch.
"""

from __future__ import annotations

import re

_PROBLEM_MARKER = re.compile(r"\b(?:problem|problem\s+is)\b", re.IGNORECASE)
_OPEN_MARKER = re.compile(r"\b(?:offen|offen\s+is)\b", re.IGNORECASE)

_CUSTOMER_CUT = re.compile(
    r"(?:"
    r"\bmit\s+der\s+kundin\b|\bmit\s+dem\s+kunden?\b|\bmit\s+der\s+bauherrin\b|\bmit\s+dem\s+bauherr(?:in)?\b|"
    r"\bkundin\b|\bkunde\b|\bkunden\b|\bbauherrin\b|\bbauherr(?:in)?\b|\bbauleitung\b|\bauftraggeber\b|"
    r"\bkundengespräch\b|\bkundengespraech\b|\bgesprochen\b|\bgred\b|\bunterhalten\b|\bzufrieden\b|\bhappy\b"
    r")",
    re.IGNORECASE,
)

_WORK_POLLUTION = re.compile(
    r"\b("
    r"gelegt|verlegt|montiert|eingebaut|gebaut|gemacht|gegossen|geschalt|"
    r"pflaster|fliesen|beton|schotter|mauerwerk|schalung|bewehrung|"
    r"erdarbeiten|graben|heizkörper|heizkoerper|wc|putz|trockenbau|"
    r"quadratmeter|quadrat|kubikmeter|kubik"
    r")\b|"
    r"\d+(?:[.,]\d+)?\s*(?:qm|m²|m2|quadratmeter|kubik|m³|m3|lfm|meter)\b",
    re.IGNORECASE,
)

_PROBLEM_SUBSTANCE = re.compile(
    r"\b("
    r"lieferung|lieferwagen|regenwasser|regen|wetter|drainage|material|fehlt|fehlen|verzöger|verzoeger|"
    r"defekt|kaputt|stör|stoer|knapp|spät|spaet|nicht\s+da|reklam|mangel|"
    r"wasserdruck|armatur|undicht|leck|frost|grundwasser|betonpumpe|gerüst|geruest|"
    r"wind|staub|temperatur|gefälle|gefaelle|riss|dichtung|manometer|pressfitting|"
    r"schrauben|mörtel|moertel|genehmigung|leitungs|kran|anlegeplatz|profil|"
    r"abpumpen|verspät|verspaet|lotrecht|schnitt|dichtband|strom"
    r")\b",
    re.IGNORECASE,
)

_OPEN_SUBSTANCE = re.compile(
    r"\b("
    r"rest|reihe|morgen|montag|dienstag|mittwoch|donnerstag|freitag|samstag|"
    r"woche|nachliefer|nachbestell|klär|klaer|fehlt\s+noch|muss\s+noch|"
    r"armatur|fuge|fliese|pflaster|schotter|putz|decke|wand|kante|abschluss|"
    r"spachtel|rigips|silikon|entlüftung|entlueftung|dämmung|daemmung|"
    r"einbau|fugen|heizung|unterlagen|freigabe|korrektur|abziehen|abbinden|"
    r"endkappe|materialumschlag|heizphase|verbindung|elektriker|asphalt|"
    r"rohrleitung|drainage|anschluss|trocknung|nacharbeit|ausgleich|armierung"
    r")\b",
    re.IGNORECASE,
)


def _normalize_probe(text: str) -> str:
    t = re.sub(r"\s+", " ", str(text or "").strip())
    t = re.sub(r"\bproblem\s+is\b", "problem", t, flags=re.IGNORECASE)
    t = re.sub(r"\boffen\s+is\b", "offen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bspaet\b", "spät", t, flags=re.IGNORECASE)
    t = re.sub(r"\bnaechste\b", "nächste", t, flags=re.IGNORECASE)
    t = re.sub(r"\bmontag\b", "Montag", t, flags=re.IGNORECASE)
    return t


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.casefold().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _has_customer_marker(text: str) -> bool:
    return bool(_CUSTOMER_CUT.search(str(text or "")))


def _is_work_polluted(text: str) -> bool:
    t = str(text or "").casefold().strip()
    if not t:
        return False
    if re.search(r"\bnoch\s+offen\b", t, flags=re.IGNORECASE) and not re.search(
        r"\b(?:verlegt|gelegt|eingebaut|montiert|aufgetragen|gegossen|geschalt)\b",
        t,
        flags=re.IGNORECASE,
    ):
        return False
    return bool(_WORK_POLLUTION.search(t))


def _cut_before_customer(text: str) -> str:
    m = _CUSTOMER_CUT.search(str(text or ""))
    if not m:
        return str(text or "").strip()
    return str(text or "")[: m.start()].strip(" .,;:")


def _cut_before_open(text: str) -> str:
    m = _OPEN_MARKER.search(str(text or ""))
    if not m:
        return str(text or "").strip()
    return str(text or "")[: m.start()].strip(" .,;:")


def _cut_before_problem(text: str) -> str:
    m = _PROBLEM_MARKER.search(str(text or ""))
    if not m:
        return str(text or "").strip()
    return str(text or "")[: m.start()].strip(" .,;:")


def _is_problem_item_polluted(item: str, raw_text: str) -> bool:
    t = str(item or "").strip()
    if not t:
        return True
    if _is_work_polluted(t):
        return True
    if _has_customer_marker(t):
        return True
    if _PROBLEM_MARKER.search(t) and _OPEN_MARKER.search(t) and len(t) > 40:
        return True
    raw = _normalize_probe(raw_text)
    if raw and t.casefold() == raw.casefold():
        return True
    if raw and len(t) > 60 and t.casefold() in raw.casefold() and _is_work_polluted(t):
        return True
    return False


def _is_open_item_polluted(item: str, raw_text: str) -> bool:
    t = str(item or "").strip()
    if not t:
        return True
    if _is_work_polluted(t):
        return True
    if _has_customer_marker(t):
        return True
    if _PROBLEM_MARKER.search(t) and _OPEN_MARKER.search(t) and len(t) > 40:
        return True
    raw = _normalize_probe(raw_text)
    if raw and t.casefold() == raw.casefold():
        return True
    if raw and len(t) > 60 and t.casefold() in raw.casefold() and _is_work_polluted(t):
        return True
    return False


def _has_problem_substance(text: str) -> bool:
    t = str(text or "").strip()
    if not t:
        return False
    if _PROBLEM_SUBSTANCE.search(t):
        return True
    return bool(_PROBLEM_MARKER.search(t) and len(t) > 8)


def _has_open_substance(text: str) -> bool:
    t = str(text or "").strip()
    if not t:
        return False
    if _OPEN_SUBSTANCE.search(t):
        return True
    return bool(_OPEN_MARKER.search(t) and len(t) > 5)


def _polish_problem_clause(text: str) -> str:
    t = _normalize_probe(text).strip(" .,;:!?")
    t = re.sub(r"^problem\b\s*:?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^es\s+gibt\s+", "", t, flags=re.IGNORECASE)
    t = t.strip(" .,;")
    if not t:
        return ""
    t = re.sub(r"\blieferung\s+kam\s+spät\b", "Lieferung kam verspätet", t, flags=re.IGNORECASE)
    t = re.sub(r"\blieferung\s+kam\s+spaet\b", "Lieferung kam verspätet", t, flags=re.IGNORECASE)
    t = re.sub(r"\bregen\b", "Regen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bdrainage\b", "Drainage", t, flags=re.IGNORECASE)
    if t and t[0].islower():
        t = t[0].upper() + t[1:]
    if not t.endswith("."):
        t += "."
    return t


def _polish_open_clause(text: str) -> str:
    t = _normalize_probe(text).strip(" .,;:!?")
    t = re.sub(r"^offen\b\s*:?\s*", "", t, flags=re.IGNORECASE)
    t = t.strip(" .,;")
    if not t:
        return ""
    t = re.sub(r"\brest\s+montag\b", "Rest am Montag noch offen", t, flags=re.IGNORECASE)
    t = re.sub(r"\brest\s+nächste\s+woche\b", "Rest nächste Woche noch offen", t, flags=re.IGNORECASE)
    t = re.sub(r"\brest\s+naechste\s+woche\b", "Rest nächste Woche noch offen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bletzte\s+reihe\s+morgen\b", "Letzte Reihe morgen noch offen", t, flags=re.IGNORECASE)
    if not re.search(r"\boffen\b", t, flags=re.IGNORECASE):
        if t and t[0].islower():
            t = t[0].upper() + t[1:]
        t = f"{t} noch offen"
    elif t and t[0].islower():
        t = t[0].upper() + t[1:]
    if not t.endswith("."):
        t += "."
    return t


def extract_problems_from_text(raw_text: str) -> list[str]:
    text = _normalize_probe(raw_text)
    if not _PROBLEM_MARKER.search(text):
        return []

    fragments: list[str] = []
    for match in _PROBLEM_MARKER.finditer(text):
        tail = text[match.end() :].lstrip(" :,-")
        tail = _cut_before_open(tail)
        tail = _cut_before_customer(tail)
        tail = tail.strip(" .,;")
        if tail and _has_problem_substance(tail):
            fragments.append(_polish_problem_clause(tail))

    if not fragments:
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            s = sentence.strip()
            if _PROBLEM_MARKER.search(s):
                tail = _PROBLEM_MARKER.split(s, maxsplit=1)[-1]
                tail = _cut_before_open(tail)
                tail = _cut_before_customer(tail).strip(" .,;")
                if tail and _has_problem_substance(tail):
                    fragments.append(_polish_problem_clause(tail))

    return _dedupe(fragments)


def extract_open_items_from_text(raw_text: str) -> list[str]:
    text = _normalize_probe(raw_text)
    if not _OPEN_MARKER.search(text):
        return []

    fragments: list[str] = []
    for match in _OPEN_MARKER.finditer(text):
        tail = text[match.end() :].lstrip(" :,-")
        tail = _cut_before_customer(tail)
        tail = _cut_before_problem(tail)
        tail = tail.strip(" .,;")
        if tail and _has_open_substance(tail):
            fragments.append(_polish_open_clause(tail))

    if not fragments:
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            s = sentence.strip()
            if _OPEN_MARKER.search(s):
                tail = _OPEN_MARKER.split(s, maxsplit=1)[-1]
                tail = _cut_before_customer(tail).strip(" .,;")
                if tail and _has_open_substance(tail):
                    fragments.append(_polish_open_clause(tail))

    return _dedupe(fragments)


def _force_extract_problems(raw_text: str) -> list[str]:
    text = _normalize_probe(raw_text)
    fragments: list[str] = []
    for match in _PROBLEM_MARKER.finditer(text):
        tail = text[match.end() :].lstrip(" :,-")
        tail = _cut_before_open(tail)
        tail = _cut_before_customer(tail).strip(" .,;")
        if tail:
            fragments.append(_polish_problem_clause(tail))
    return _dedupe(fragments)


def _force_extract_open_items(raw_text: str) -> list[str]:
    text = _normalize_probe(raw_text)
    fragments: list[str] = []
    for match in _OPEN_MARKER.finditer(text):
        tail = text[match.end() :].lstrip(" :,-")
        tail = _cut_before_customer(tail)
        tail = _cut_before_problem(tail).strip(" .,;")
        if tail:
            fragments.append(_polish_open_clause(tail))
    return _dedupe(fragments)


def enrich_thin_problem_item(text: str) -> str:
    t = _polish_problem_clause(text)
    if not t:
        return ""
    low = t.casefold()
    if _has_problem_substance(t):
        return t
    if re.search(r"\bregen\b", low):
        return "Regen als Wetterproblem."
    return t


def enrich_thin_open_item(text: str) -> str:
    t = _polish_open_clause(text)
    if not t:
        return ""
    if re.search(r"\boffen\b", t, flags=re.IGNORECASE):
        return t
    return _polish_open_clause(t)


def refine_problems_list(existing: list[str], raw_text: str) -> list[str]:
    raw_items = [str(x).strip() for x in (existing or []) if str(x).strip()]
    extracted = extract_problems_from_text(raw_text)

    if raw_items and all(not _is_problem_item_polluted(x, raw_text) for x in raw_items):
        polished = [_polish_problem_clause(x) for x in raw_items if _has_problem_substance(x)]
        polished = [enrich_thin_problem_item(x) for x in polished if x]
        return _dedupe(polished)

    if extracted:
        return extracted

    if any(_is_problem_item_polluted(x, raw_text) for x in raw_items):
        forced = _force_extract_problems(raw_text)
        if forced:
            return forced
        return []

    polished = [_polish_problem_clause(x) for x in raw_items if _has_problem_substance(x)]
    polished = [enrich_thin_problem_item(x) for x in polished if x]
    return _dedupe(polished)


def refine_open_items_list(existing: list[str], raw_text: str) -> list[str]:
    raw_items = [str(x).strip() for x in (existing or []) if str(x).strip()]
    extracted = extract_open_items_from_text(raw_text)

    if raw_items and all(not _is_open_item_polluted(x, raw_text) for x in raw_items):
        polished = [_polish_open_clause(x) for x in raw_items if _has_open_substance(x)]
        polished = [enrich_thin_open_item(x) for x in polished if x]
        return _dedupe(polished)

    if extracted:
        return extracted

    if any(_is_open_item_polluted(x, raw_text) for x in raw_items):
        forced = _force_extract_open_items(raw_text)
        if forced:
            return forced
        return []

    polished = [_polish_open_clause(x) for x in raw_items if _has_open_substance(x)]
    polished = [enrich_thin_open_item(x) for x in polished if x]
    return _dedupe(polished)
