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
    r"abpumpen|verspät|verspaet|lotrecht|schnitt|dichtband|strom|"
    r"untergrund|uneben|abbrechen|unterbrochen|regnen|geregnet|staub|lieferung|pressfitting|"
    r"kleber|hitze|anschluss|eng|grundwasser|probleme?"
    r")\b",
    re.IGNORECASE,
)

_OPEN_SUBSTANCE = re.compile(
    r"\b("
    r"rest|reihe|morgen|montag|dienstag|mittwoch|donnerstag|freitag|samstag|"
    r"woche|nachliefer|nachbestell|klär|klaer|fehlt\s+noch|muss\s+noch|müssen\s+wir|muessen\s+wir|"
    r"armatur|fuge|fliese|pflaster|schotter|putz|decke|wand|kante|abschluss|"
    r"spachtel|rigips|silikon|entlüftung|entlueftung|dämmung|daemmung|oberputz|unterputz|"
    r"einbau|fugen|heizung|unterlagen|freigabe|korrektur|abziehen|abbinden|"
    r"endkappe|materialumschlag|heizphase|verbindung|elektriker|asphalt|"
    r"rohrleitung|drainage|anschluss|trocknung|nacharbeit|ausgleich|armierung|"
    r"hecke|schneiden|abschließen|abschliessen|grundieren|grundiert"
    r")\b",
    re.IGNORECASE,
)

_IMPLICIT_PROBLEM_INTERRUPT = re.compile(
    r"(?:"
    r"(?:leider\s+)?mussten\s+wir\s+die\s+arbeiten\s+(?:abbrechen|abrechnen)\s+weil\s+es\s+(?:stark\s+)?angefangen(?:\s+hat)?\s+zu\s+regnen"
    r"|(?:leider\s+)?(?:wir\s+)?mussten\s+(?:die\s+)?arbeiten?\s+(?:abbrechen|abrechnen|stoppen|beenden)"
    r"|(?:leider\s+)?wir\s+mussten\s+(?:die\s+)?arbeiten?\s+(?:abbrechen|abrechnen|stoppen|beenden)"
    r"|(?:mussten\s+wir|hamma)\s+(?:[^.!?]{0,70}?)?(?:die\s+)?arbeiten?\s+(?:abbrechen|abrechnen|stoppen|beenden)"
    r"|(?:leider\s+)?mussten\s+wir\s+abbrechen(?:\s+(?:morgen|weil|da|denn))?"
    r"|mussten\s+leider\s+abbrechen(?:\s+(?:weil|da|morgen))?"
    r"|mussten\s+abbrechen\s+(?:weil|da|morgen)\s+[^.!?]{0,80}"
    r"|mussten\s+abbrechen\s+(?:weil|da)\s+[^.!?]{4,80}"
    r"|(?:leider\s+)?(?:mussten|müssen)\s+(?:wir\s+)?stoppen\s+(?:weil|da)\s+[^.!?]{4,80}"
    r"|(?:weil|da)\s+es\s+(?:stark\s+)?angefangen(?:\s+hat)?\s+zu\s+regnen"
    r"|angefangen(?:\s+hat)?\s+zu\s+regnen"
    r"|(?:das\s+war\s+)?(?:ein\s+)?(?:sehr\s+)?großes\s+problem"
    r"|untergrund\s+(?:war\s+)?(?:sehr\s+)?uneben(?:\s+was\s+zu\s+problemen\s+geführt\s+hat)?"
    r"|(?:die\s+)?wand\s+(?:war\s+)?(?:sehr\s+)?uneben(?:\s+was\s+zu\s+problemen\s+geführt\s+hat)?"
    r"|(?:die\s+)?wand\s+(?:war\s+)?nicht\s+lotrecht(?:\s+was\s+zu\s+problemen\s+geführt\s+hat)?"
    r"|was\s+zu\s+problemen\s+geführt\s+hat"
    r"|(?:weil|da)\s+(?:die\s+)?wand\s+nicht\s+lotrecht\s+ist"
    r"|(?:leider\s+)?maschine\s+kaputt\s+mussten\s+stoppen"
    r"|leider\s+[^.!?]{0,50}regen[^.!?]{0,50}abbrechen"
    r"|(?:leider|wegen)\s+[^.!?]{0,80}(?:regen|wetter|sturm|frost|kaputt|defekt|undicht|staub|liefer)"
    r"|(?:zu\s+)?(?:spaet|spät)(?:er)?\s+(?:kam|geliefert|geworden)"
    r"|(?:dichtung|pressfitting)\s+[^.!?]{0,40}(?:undicht|fehlt)"
    r"|grundwasser\s+[^.!?]{0,40}(?:stand|im\s+graben)"
    r"|gefälle\s+(?:war\s+)?(?:falsch|zu\s+flach)"
    r"|(?:leider|wegen)\s+[^.!?]{0,40}material\s+knapp"
    r"|keine\s+arbeit\s+wegen\s+regen"
    r"|viel\s+geregnet"
    r"|geregnet[^.!?]{0,50}arbeit\s+stopp"
    r"|arbeit\s+stopp"
    r")",
    re.IGNORECASE,
)

_IMPLICIT_OPEN_FUTURE = re.compile(
    r"(?:"
    r"morgen\s+(?:müssen\s+wir|muessen\s+wir|muss\s+ich|müssen)\s+(?:noch\s+)?[^.!?]{4,120}"
    r"|morgen\s+(?:noch\s+)?[^.!?]{4,120}(?:schneiden|legen|verlegen|auftragen|abschließen|abschliessen|"
    r"montieren|fertigstellen|fertig\s+machen|machen|erledigen|weitermachen|schalen|abziehen|verfuellen|verfüllen|"
    r"einbauen|asphaltieren|asphaltiert|weiter)"
    r"|morgen\s+weiter[^.!?]{0,60}"
    r"|warten\s+auf[^.!?]{0,80}(?:nächste|naechste)\s+woche"
    r"|(?:noch\s+)?walzen\s+(?:nächste|naechste)\s+woche"
    r"|morgen\s+(?:noch\s+)?(?:letzte|rest)[^.!?]{0,80}"
    r"|morgen\s+noch\s+[^.!?]{4,80}"
    r"|(?:am\s+)?(?:montag|dienstag|mittwoch|donnerstag|freitag|samstag)\s+"
    r"(?:müssen\s+wir|muessen\s+wir|noch\s+)?[^.!?]{4,120}"
    r"|dementsprechend\s+(?:werden\s+wir|machen\s+wir|schliessen\s+wir|schließen\s+wir|betonieren\s+wir)\s+morgen[^.!?]{0,80}"
    r"|(?:dementsprechend\s+)?(?:pflaster\w*\s+)?verschiebt\s+sich\s+[^.!?]{4,80}?\b(?:auf\s+)?morgen\b"
    r"|(?:verlegt|verschoben|verlagert|verlägert)\s+(?:auf\s+)?morgen[^.!?]{0,60}"
    r"|(?:dementsprechend\s+)?(?:pflaster\w*\s+)?verschiebt\s+sich\s+[^.!?]{4,80}?\b(?:auf\s+)?(?:montag|dienstag|mittwoch|donnerstag|freitag|samstag)\b"
    r"|rest\s+[^.!?]{0,40}?\bpflaster\b[^.!?]{0,40}?\bmorgen\b"
    r"|pflaster\b[^.!?]{0,40}?\bmorgen\b[^.!?]{0,40}?\b(?:legen|verlegen|fertig)\b"
    r"|\bund\s+morgen\s+[^.!?]{0,40}?\bpflaster\b"
    r"|\bpflaster\s+morgen\b"
    r"|\bpflaster\w*\s+morgen\b"
    r")",
    re.IGNORECASE,
)


def _normalize_probe(text: str) -> str:
    t = re.sub(r"\s+", " ", str(text or "").strip())
    t = re.sub(r"\bproblem\s+is\b", "problem", t, flags=re.IGNORECASE)
    t = re.sub(r"\boffen\s+is\b", "offen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bspaet\b", "spät", t, flags=re.IGNORECASE)
    t = re.sub(r"\bnaechste\b", "nächste", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgefaelle\b", "gefälle", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgefuehrt\b", "geführt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bmontag\b", "Montag", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(die\s+)?arbeiten?\s+abrechnen\b",
        lambda m: f"{m.group(1) or ''}Arbeiten abbrechen".strip(),
        t,
        flags=re.IGNORECASE,
    )
    # Gebrochenes Deutsch: "Arbeit stopp" / "viel Regen" (ohne korrektes Verb).
    t = re.sub(r"\barbeit\s+stopp\b", "arbeiten gestoppt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bviel\s+regen\b", "viel geregnet", t, flags=re.IGNORECASE)
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


def _is_legitimate_future_work(text: str) -> bool:
    t = str(text or "").casefold()
    return bool(
        re.search(
            r"\b(?:morgen|montag|dienstag|mittwoch|donnerstag|freitag|samstag|"
            r"nächste\s+woche|naechste\s+woche|müssen\s+wir|muessen\s+wir|"
            r"muss\s+noch|noch\s+offen|weitermachen|abschließen|abschliessen)\b",
            t,
            flags=re.IGNORECASE,
        )
    )


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


def _cut_before_morgen(text: str) -> str:
    m = re.search(r"\bmorgen\b", str(text or ""), flags=re.IGNORECASE)
    if m and m.start() > 8:
        return str(text or "")[: m.start()].strip(" .,;:")
    return str(text or "").strip()


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
    if _is_legitimate_future_work(t) and not re.search(
        r"\b(?:regen|kaputt|defekt|undicht|uneben|stör|stoer|problem|unterbrochen|abbrechen)\b",
        t,
        flags=re.IGNORECASE,
    ):
        return True
    if re.search(r"\b(?:dementsprechend|weitermachen)\b", t, flags=re.IGNORECASE) and not _has_problem_substance(t):
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
    if len(t) > 85:
        return True
    if re.search(r"\bheute\b", t, flags=re.IGNORECASE) and re.search(r"\bmorgen\b", t, flags=re.IGNORECASE):
        return True
    if _is_work_polluted(t) and not _is_legitimate_future_work(t):
        return True
    if _is_work_polluted(t) and re.search(
        r"\b(?:eingebaut|verlegt|montiert|gelegt|aufgetragen|gebaut|geschlossen)\b",
        t,
        flags=re.IGNORECASE,
    ):
        return True
    if _is_work_polluted(t) and re.search(
        r"\d+(?:[.,]\d+)?\s*(?:qm|m²|m2|quadratmeter|meter)\b",
        t,
        flags=re.IGNORECASE,
    ):
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
    if re.search(r"lieferung\s+schotter\s+sp", t, flags=re.IGNORECASE):
        return "Lieferung Schotter verspätet."
    t = re.sub(r"\bregen\b", "Regen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bdrainage\b", "Drainage", t, flags=re.IGNORECASE)
    if re.search(r"^regen\s+heute\s+keine\s+arbeit", t, flags=re.IGNORECASE):
        return "Keine Arbeit wegen Regen."
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
    m_pfl = re.search(
        r"morgen\s+(?:müssen\s+wir|muessen\s+wir|muss\s+ich)\s+(?:noch\s+)*(?:dann\s+)*(?:auch\s+)*"
        r"(\d+(?:[.,]\d+)?\s*(?:m²|m2|qm|quadratmeter)\s+)?pflaster\s+legen",
        t,
        flags=re.IGNORECASE,
    )
    if m_pfl:
        qty = (m_pfl.group(1) or "").strip()
        lead = f"Morgen müssen wir noch {qty} Pflaster legen".strip()
        lead = re.sub(r"\s+", " ", lead)
        return f"{lead} noch offen."
    m_fugen = re.search(
        r"(?:morgen\s+)?(?:müssen\s+wir|muessen\s+wir|muss\s+ich)\s+(?:dann\s+)?(?:noch\s+mal\s+)?"
        r"(?:zur\s+baustelle\s+und\s+)?(?:die\s+)?fugen\s+mit\s+fugensand\s+f(?:ü|ue|u)llen",
        t,
        flags=re.IGNORECASE,
    )
    if m_fugen:
        return "Morgen Fugen mit Fugensand füllen noch offen."
    m_abort_pfl = re.search(
        r"\b(?:wollten|wollen|wollte)\b[^.!?]{0,140}?\b(?:mit\s+dem\s+)?pflaster\w*\b[^.!?]{0,80}?\banfangen\b"
        r"[^.!?]{0,50}?(?:fuer|für)\s+(?P<qty>\d+(?:[.,]\d+)?\s*(?:m²|m2|qm)?)",
        t,
        flags=re.IGNORECASE,
    )
    if m_abort_pfl:
        qty = (m_abort_pfl.group("qty") or "").strip()
        if qty:
            return f"{qty} Pflaster verlegen noch offen."
        return "Pflasterarbeiten noch offen."
    m_shift = re.search(
        r"(?:dementsprechend\s+)?verschiebt\s+sich\s+(?:das\s+)?([^.,;!?]+?)\s+auf\s+morgen",
        t,
        flags=re.IGNORECASE,
    )
    if m_shift:
        work = str(m_shift.group(1) or "").strip()
        if work:
            work = work[0].upper() + work[1:]
        return f"{work} auf morgen verschoben noch offen."
    m_shift_day = re.search(
        r"(?:dementsprechend\s+)?verschiebt\s+sich\s+(?:das\s+)?([^.,;!?]+?)\s+auf\s+"
        r"(montag|dienstag|mittwoch|donnerstag|freitag|samstag)",
        t,
        flags=re.IGNORECASE,
    )
    if m_shift_day:
        work = str(m_shift_day.group(1) or "").strip()
        day = str(m_shift_day.group(2) or "").strip().capitalize()
        if work:
            work = work[0].upper() + work[1:]
        return f"{work} auf {day} verschoben noch offen."
    m_pfl_morgen = re.search(r"\b(pflaster\w*)\s+morgen\b", t, flags=re.IGNORECASE)
    if m_pfl_morgen:
        work = str(m_pfl_morgen.group(1) or "").strip()
        if work:
            work = work[0].upper() + work[1:]
        return f"{work} morgen noch offen."
    m_shift_rev = re.search(
        r"\b(pflaster\w*)\s+verschiebt\s+sich\s+auf\s+"
        r"(montag|dienstag|mittwoch|donnerstag|freitag|samstag|morgen)",
        t,
        flags=re.IGNORECASE,
    )
    if m_shift_rev:
        work = str(m_shift_rev.group(1) or "").strip()
        day = str(m_shift_rev.group(2) or "").strip().capitalize()
        if work:
            work = work[0].upper() + work[1:]
        if day.casefold() == "morgen":
            return f"{work} auf morgen verschoben noch offen."
        return f"{work} auf {day} verschoben noch offen."
    t = re.sub(r"\b(dann|auch|halt|eben|mal)\b", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip(" .,;")
    t = re.sub(r"\s+noch\s+offen\.?$", "", t, flags=re.IGNORECASE).strip(" .,;")
    t = re.sub(r"\brest\s+montag\b", "Rest am Montag noch offen", t, flags=re.IGNORECASE)
    t = re.sub(r"\brest\s+nächste\s+woche\b", "Rest nächste Woche noch offen", t, flags=re.IGNORECASE)
    t = re.sub(r"\brest\s+naechste\s+woche\b", "Rest nächste Woche noch offen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bletzte\s+reihe\s+morgen\b", "Letzte Reihe morgen noch offen", t, flags=re.IGNORECASE)
    t = re.sub(
        r"^morgen\s+müssen\s+wir\s+(?:noch\s+)?",
        "Morgen müssen wir noch ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"^morgen\s+muessen\s+wir\s+(?:noch\s+)?",
        "Morgen müssen wir noch ",
        t,
        flags=re.IGNORECASE,
    )
    if not re.search(r"\boffen\b", t, flags=re.IGNORECASE):
        if t and t[0].islower():
            t = t[0].upper() + t[1:]
        t = f"{t} noch offen"
    elif t and t[0].islower():
        t = t[0].upper() + t[1:]
    t = re.sub(r"\bnoch\s+noch\b", "noch", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip()
    if not t.endswith("."):
        t += "."
    return t


def _implicit_problem_clause(match_text: str) -> str:
    t = _normalize_probe(match_text).strip(" .,;")
    low = t.casefold()
    if re.search(r"weil\s+es|angefangen\s+hat\s+zu\s+regnen|geregnet\s+hat|viel\s+geregnet", low):
        return _polish_problem_clause("Arbeiten wegen Regen unterbrochen")
    if re.search(r"geregnet", low) and re.search(r"stopp|gestoppt|abbrechen|beenden", low):
        return _polish_problem_clause("Arbeiten wegen Regen unterbrochen")
    if re.search(r"abbrechen|abrechnen|stoppen", low) and re.search(r"regen|angefangen\s+hat\s+zu", low):
        return _polish_problem_clause("Arbeiten wegen Regen unterbrochen")
    if re.search(r"abbrechen|stoppen", low) and re.search(r"staub", low):
        return _polish_problem_clause("Arbeiten wegen Staub unterbrochen")
    if re.search(r"abbrechen|stoppen", low) and re.search(r"liefer|spät|spaet", low):
        return _polish_problem_clause("Lieferung verspätet, Arbeiten unterbrochen")
    if re.search(r"undicht|dichtung", low):
        return _polish_problem_clause("Dichtung undicht")
    if re.search(r"pressfitting\s+fehlt|fehlt", low) and re.search(r"pressfitting", low):
        return _polish_problem_clause("Pressfitting fehlt")
    if re.search(r"zu\s+eng|anschluss\s+zu\s+eng", low):
        return _polish_problem_clause("Anschluss zu eng")
    if re.search(r"grundwasser", low):
        return _polish_problem_clause("Grundwasser im Graben")
    if re.search(r"gefälle|gefaelle", low):
        return _polish_problem_clause("Gefälle nicht in Ordnung")
    if re.search(r"lotrecht", low):
        return _polish_problem_clause("Wand nicht lotrecht")
    if re.search(r"was\s+zu\s+problemen\s+gef", low):
        return _polish_problem_clause("Es gab Probleme auf der Baustelle")
    if re.search(r"abbrechen|stoppen|beenden", low) and re.search(r"kleber|hitze|abbindet", low):
        return _polish_problem_clause("Kleber bindet bei Hitze zu schnell ab")
    if re.search(r"material\s+knapp", low):
        return _polish_problem_clause("Material knapp")
    if re.search(r"keine\s+arbeit\s+wegen\s+regen", low):
        return _polish_problem_clause("Keine Arbeit wegen Regen")
    if re.search(r"abbrechen|stoppen|beenden", low):
        return _polish_problem_clause("Arbeiten mussten unterbrochen werden")
    if re.search(r"uneben", low) or (
        re.search(r"zu\s+problemen", low) and re.search(r"(?:untergrund|wand)", low)
    ):
        return _polish_problem_clause("Untergrund sehr uneben")
    if re.search(r"großes\s+problem|grosses\s+problem", low):
        if re.search(r"liefer", low):
            return _polish_problem_clause("Problem mit der Lieferung")
        return _polish_problem_clause("Es gab ein Problem auf der Baustelle")
    if re.search(r"schlechtem\s+wetter|wetter", low):
        return _polish_problem_clause("Schlechtes Wetter")
    return _polish_problem_clause(t)


def _extract_implicit_problems(raw_text: str) -> list[str]:
    text = _normalize_probe(raw_text)
    if not text:
        return []
    fragments: list[str] = []
    # Volltext und Kunden-Vorschnitt: Probleme nach Kundengespräch (z. B. Maschine kaputt)
    # dürfen nicht verloren gehen.
    for probe in (text, _cut_before_customer(text)):
        if not probe:
            continue
        for match in _IMPLICIT_PROBLEM_INTERRUPT.finditer(probe):
            chunk = re.split(r"\bmorgen\b", match.group(0), maxsplit=1, flags=re.IGNORECASE)[0].strip(" .,;")
            clause = _implicit_problem_clause(chunk)
            if clause and _has_problem_substance(clause):
                fragments.append(clause)
    cleaned = [f for f in fragments if not re.match(r"^Weil\b", f.strip())]
    if cleaned:
        fragments = cleaned
    return _dedupe(fragments)


def _extract_implicit_open_items(raw_text: str) -> list[str]:
    text = _cut_before_customer(_normalize_probe(raw_text))
    if not text:
        return []
    fragments: list[str] = []
    for match in _IMPLICIT_OPEN_FUTURE.finditer(text):
        chunk = match.group(0).strip(" .,;")
        chunk = _cut_before_customer(chunk)
        chunk = re.split(r"\b(?:problem|leider\s+mussten)\b", chunk, maxsplit=1, flags=re.IGNORECASE)[0]
        chunk = chunk.strip(" .,;")
        if len(chunk) > 100:
            m = re.search(
                r"(?:morgen\s+(?:müssen\s+wir|muessen\s+wir)\s+(?:noch\s+)?.+|"
                r"dementsprechend\s+werden\s+wir\s+morgen.+)",
                chunk,
                flags=re.IGNORECASE,
            )
            chunk = m.group(0).strip(" .,;") if m else chunk[:100].strip(" .,;")
        if chunk and _has_open_substance(chunk):
            fragments.append(_polish_open_clause(chunk))
    if not fragments and _raw_paving_aborted_for_open(text):
        m = re.search(
            r"\b(?:wollten|wollen|wollte)\b[^.!?]{0,140}?\b(?:mit\s+dem\s+)?pflaster\w*\b[^.!?]{0,80}?\banfangen\b"
            r"[^.!?]{0,50}?(?:fuer|für)\s+(?P<qty>\d+(?:[.,]\d+)?\s*(?:m²|m2|qm)?)",
            text,
            flags=re.IGNORECASE,
        )
        if m:
            fragments.append(_polish_open_clause(m.group(0)))
    return _dedupe(fragments)


def _raw_paving_aborted_for_open(text: str) -> bool:
    raw = str(text or "").casefold()
    return bool(
        re.search(
            r"\b(wollten|wollen|wollte)\b.{0,140}\bpflaster\w*\b.{0,80}\banfangen\b",
            raw,
        )
        and re.search(
            r"\b(abbrechen|unterbrochen|angefangen\s+(?:hat\s+)?zu\s+regnen|strich\s+durch\s+die\s+rechnung)\b",
            raw,
        )
    )


def extract_problems_from_text(raw_text: str) -> list[str]:
    text = _normalize_probe(raw_text)
    fragments: list[str] = []

    if _PROBLEM_MARKER.search(text):
        for match in _PROBLEM_MARKER.finditer(text):
            tail = text[match.end() :].lstrip(" :,-")
            tail = _cut_before_open(tail)
            tail = _cut_before_morgen(tail)
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
                    tail = _cut_before_morgen(tail)
                    tail = _cut_before_customer(tail).strip(" .,;")
                    if tail and _has_problem_substance(tail):
                        fragments.append(_polish_problem_clause(tail))

    if not fragments:
        fragments = _extract_implicit_problems(raw_text)

    full = _normalize_probe(raw_text)
    for pattern, label in (
        (r"keine\s+arbeit\s+wegen\s+regen", "Keine Arbeit wegen Regen"),
        (r"(?:leider|wegen)\s+[^.!?]{0,40}material\s+knapp", "Material knapp"),
    ):
        if re.search(pattern, full, flags=re.IGNORECASE):
            clause = _polish_problem_clause(label)
            if clause:
                fragments.append(clause)

    return _dedupe(fragments)


def extract_open_items_from_text(raw_text: str) -> list[str]:
    text = _normalize_probe(raw_text)
    fragments: list[str] = []

    if _OPEN_MARKER.search(text):
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

    if not fragments:
        fragments = _extract_implicit_open_items(raw_text)

    return _dedupe(fragments)


def _force_extract_problems(raw_text: str) -> list[str]:
    forced = _force_extract_problems_markers(raw_text)
    if forced:
        return forced
    return _extract_implicit_problems(raw_text)


def _force_extract_problems_markers(raw_text: str) -> list[str]:
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
    forced = _force_extract_open_items_markers(raw_text)
    if forced:
        return forced
    return _extract_implicit_open_items(raw_text)


def _force_extract_open_items_markers(raw_text: str) -> list[str]:
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
