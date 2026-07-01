"""Extraktion und Formulierung von Kundengespräch aus Rohtext.

Rein additiv: trennt Arbeitstext von Kundeninhalt und formuliert knapp/professionell.
"""

from __future__ import annotations

import re

_CUSTOMER_MARKERS = re.compile(
    r"\b("
    r"kundin|kunde|kunden|bauherr|bauherrin|bauleitung|auftraggeber|"
    r"kundengespräch|kundengespraech|unterhalten|gesprochen|gred|"
    r"zufrieden|freut\s+sich|weitere\s+aufträge|weitere\s+auftraege|"
    r"abgesprochen|abgestimmt|informiert|rücksprache|ruecksprache|"
    r"meckert|beschwert|einwand|einverstanden|happy"
    r")\b",
    re.IGNORECASE,
)

_CUSTOMER_START = re.compile(
    r"(?:"
    r"mit\s+der\s+kundin|mit\s+dem\s+kunden|mit\s+der\s+bauherrin|mit\s+dem\s+bauherr|"
    r"mit\s+dem\s+auftraggeber|mit\s+der\s+bauleitung|"
    r"kundengespräch|kundengespraech|"
    r"die\s+kundin|der\s+kunde|die\s+kunden|dem\s+kunden|"
    r"bauherr\s+war|bauherrin\s+war|bauleitung\s+war"
    r")",
    re.IGNORECASE,
)

_WORK_POLLUTION = re.compile(
    r"\b("
    r"gelegt|verlegt|montiert|eingebaut|gebaut|gemacht|gegossen|geschalt|gesetzt|"
    r"pflaster|fliesen|beton|schotter|mauerwerk|schalung|bewehrung|palisaden|"
    r"erdarbeiten|graben|heizkörper|heizkoerper|wc|putz|trockenbau"
    r")\b|"
    r"\d+(?:[.,]\d+)?\s*(?:qm|m²|m2|quadratmeter|kubik|m³|m3|lfm|meter)\b|"
    r"\d+\s+laufende\s+meter\b",
    re.IGNORECASE,
)

_CUSTOMER_TAIL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?:mit\s+der\s+)?bauleitung[^.!?]*(?:rücksprache|ruecksprache|informiert|abgestimmt|abgesprochen|gehalten)[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"bauherr(?:in)?\s+(?:kurz\s+)?(?:informiert|abgestimmt|gesprochen|war)[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"bauherr(?:in)?\s+zufrieden[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"bauherr(?:in)?\s+sehr\s+happy[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"auftraggeber\s+unterhalten[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"auftraggeber[^.!?]*(?:lobt|weiterempfehl|empfiehlt|auftrag)[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"nach\s+den\s+arbeiten[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"kundin\s+(?:happy|gelobt)[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"kundin[^.!?]*(?:gelobt|weiterempfehl|empfiehlt|auftrag)[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"auftraggeber\s+(?:kurz\s+)?(?:da|war|anwesend|gesprochen|gred|informiert|abgestimmt)[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"kunde\s+(?:meckert|beschwert|reklamiert)[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"kundin\s+(?:meckert|beschwert|reklamiert)[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"kunde\s+(?:informiert|war\s+einverstanden)[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"kundin\s+(?:sehr\s+|mega\s+)?zufrieden[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"kunde\s+gred\s+war\s+ok[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"kund(?:e|in)\s+(?:sehr\s+|mega\s+)?zufrieden[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:mit\s+)?dem\s+kunden?\s+gesprochen[^.!?]*zufrieden[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"rücksprache\s+mit\s+kund(?:e|in)[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"ruecksprache\s+mit\s+kund(?:e|in)[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"kunde\s+vor\s+ort[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"kunde\s+war\s+da(?:\s+und\s+happy)?[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"kundin\s+hat\s+farbe\s+bestätigt[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"kundin\s+hat\s+farbe\s+bestae?tigt[^.!?]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"kundin\s+vor\s+ort[^.!?]*",
        re.IGNORECASE,
    ),
)

_PROBLEM_OPEN_SPLIT = re.compile(r"\b(?:problem|offen)\b", re.IGNORECASE)

_TRANSITION_SPLIT = re.compile(
    r"\s+(?=(?:anschließend|anschliessend|danach|dann|im\s+anschluss|hinterher|später|spaeter|"
    r"nach\s+den\s+arbeiten)\b)",
    re.IGNORECASE,
)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def _normalize_customer_probe(text: str) -> str:
    t = _normalize_whitespace(text)
    t = re.sub(r"\bzu\s+frieden\b", "zufrieden", t, flags=re.IGNORECASE)
    t = re.sub(r"\bkund\b", "kunde", t, flags=re.IGNORECASE)
    t = re.sub(r"\bge\s+sprochen\b", "gesprochen", t, flags=re.IGNORECASE)
    t = re.sub(r"\babgred\b", "abgesprochen", t, flags=re.IGNORECASE)
    return t


def _has_customer_marker(text: str) -> bool:
    return bool(_CUSTOMER_MARKERS.search(_normalize_customer_probe(text)))


def _is_work_polluted(text: str) -> bool:
    low = str(text or "").casefold()
    if not _has_customer_marker(low):
        return False
    return bool(_WORK_POLLUTION.search(low))


_OPEN_ITEM_PREFIX = re.compile(
    r"^(?:(?:offen|noch)\s+)?"
    r"(?:fugen|silikon|spachtel|randstein|rest|kante|reihe|entlueftung|entlüftung|"
    r"anstrich|endkappe|verfuellung|verfüllung|abschluss|nacharbeit)\s+"
    r"(?:morgen|freitag|donnerstag|dienstag|samstag|montag|woche|nächste|naechste)\s+",
    re.IGNORECASE,
)


def _strip_open_item_leading_noise(text: str) -> str:
    t = _normalize_whitespace(text)
    prev = ""
    while t != prev:
        prev = t
        t = _OPEN_ITEM_PREFIX.sub("", t).strip(" .,;")
    return t


def _split_sentences(text: str) -> list[str]:
    t = _TRANSITION_SPLIT.sub(". ", str(text or "").strip())
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", t) if p.strip()]
    if len(parts) > 1:
        return parts
    single = parts[0] if parts else t
    chunks = [c.strip() for c in _PROBLEM_OPEN_SPLIT.split(single) if c.strip()]
    if len(chunks) > 1:
        return chunks
    return [single] if single else []


def _strip_problem_open_noise(text: str) -> str:
    t = _normalize_whitespace(text)
    t = re.split(r"\b(?:problem|offen)\b", t, maxsplit=1, flags=re.IGNORECASE)[0]
    t = re.sub(r"^(?:problem|offen)\b\s*", "", t, flags=re.IGNORECASE)
    return t.strip(" .,;")


def _extract_customer_tail(text: str) -> str:
    t = _normalize_customer_probe(text)
    for pattern in _CUSTOMER_TAIL_PATTERNS:
        m = pattern.search(t)
        if m:
            return _strip_problem_open_noise(m.group(0))
    m = _CUSTOMER_START.search(t)
    if m:
        return _strip_problem_open_noise(t[m.start() :])
    return ""


def _extract_customer_fragment(sentence: str) -> str:
    s = _normalize_whitespace(sentence)
    if not s or not _has_customer_marker(s):
        return ""

    m = _CUSTOMER_START.search(s)
    if m:
        return _strip_problem_open_noise(s[m.start() :])

    if _is_work_polluted(s):
        tail = _extract_customer_tail(s)
        if tail:
            return tail
        if re.search(r"\s+und\s+", s, flags=re.IGNORECASE):
            parts = [p.strip() for p in re.split(r"\s+und\s+", s, flags=re.IGNORECASE) if p.strip()]
            customer_parts = [p for p in parts if _has_customer_marker(p) and not _WORK_POLLUTION.search(p)]
            if customer_parts:
                return " und ".join(customer_parts)
        return ""

    cleaned = _strip_open_item_leading_noise(s)
    if cleaned and _has_customer_marker(cleaned):
        tail = _extract_customer_tail(cleaned)
        if tail:
            return tail
        if not _is_work_polluted(cleaned):
            return cleaned

    return s


def _detect_customer_gender(sources: list[str]) -> str:
    blob = " ".join(sources).casefold()
    if re.search(r"\b(?:die|mit\s+der)\s+kundin\b|\bbauherrin\b", blob):
        return "f"
    if re.search(r"\b(?:der|dem|mit\s+dem)\s+kunden\b|\bder\s+kunde\b|\bmit\s+dem\s+kunde\b|\bbauherr\b", blob):
        return "m"
    if re.search(r"\bkundin\b", blob):
        return "f"
    if re.search(r"\bkunde\b", blob):
        return "m"
    return "n"


def _polish_customer_clause(text: str, *, gender: str) -> str:
    t = _normalize_whitespace(text).rstrip(".,;:!?")

    t = re.sub(
        r"^(?:anschließend|anschliessend|danach|dann|im anschluss|hinterher|später|spaeter)\s+",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"^(?:haben\s+wir|hamma|wir\s+haben)\s+(?:uns\s+)?",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"^mit\s+der\s+kundin\s+unterhalten\s+und\s+",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"^mit\s+dem\s+kunden\s+unterhalten\s+und\s+",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"^uns\s+mit\s+der\s+kundin\s+unterhalten\s+und\s+",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"^mit\s+dem\s+kunden\s+gesprochen,?\s*(?:er\s+)?",
        "",
        t,
        flags=re.IGNORECASE,
    )
    if not t.strip() and re.search(r"^mit\s+dem\s+kunden\s+gesprochen\b", _normalize_whitespace(text), flags=re.IGNORECASE):
        t = "Mit dem Kunden gesprochen"
    t = re.sub(
        r"^mit\s+der\s+kundin\s+gesprochen,?\s*(?:sie\s+)?",
        "",
        t,
        flags=re.IGNORECASE,
    )
    if not t.strip() and re.search(r"^mit\s+der\s+kundin\s+gesprochen\b", _normalize_whitespace(text), flags=re.IGNORECASE):
        t = "Mit der Kundin gesprochen"
    if t and re.search(r"\bweiter\s+mit\s+uns\b", t, flags=re.IGNORECASE) and not re.search(r"\bkund", t, flags=re.IGNORECASE):
        t = re.sub(r"^möchte\b", "Der Kunde möchte", t, flags=re.IGNORECASE)
    t = re.sub(r"^die\s+kundin\s+war\b", "die Kundin ist", t, flags=re.IGNORECASE)
    t = re.sub(r"^der\s+kunde\s+war\b", "der Kunde ist", t, flags=re.IGNORECASE)
    t = re.sub(r"\bwar\s+sehr\b", "ist sehr", t, flags=re.IGNORECASE)
    t = re.sub(r"^er\s+war\b", "er ist", t, flags=re.IGNORECASE)
    t = re.sub(r"^sie\s+war\b", "sie ist", t, flags=re.IGNORECASE)
    t = re.sub(
        r"^bauherr(?:in)?\s+(?:kurz\s+)?informiert\s+alles\s+abgestimmt\b",
        "Bauherr kurz informiert, alles abgestimmt",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"^auftraggeber\s+da\b",
        "Auftraggeber war vor Ort",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"^auftraggeber\s+informiert\b",
        "Auftraggeber informiert",
        t,
        flags=re.IGNORECASE,
    )

    t = re.sub(
        r"^kunde\s+gred\s+war\s+ok\b",
        "Mit dem Kunden gesprochen, er war einverstanden",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"^kunde\s+war\s+da(?:\s+und\s+happy)?\b",
        "Der Kunde war vor Ort und war zufrieden",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"^kundin\s+hat\s+farbe\s+bestätigt\b",
        "Die Kundin hat die Farbe bestätigt",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"^kundin\s+(?:sehr\s+|mega\s+)?zufrieden\b",
        "Die Kundin ist sehr zufrieden",
        t,
        flags=re.IGNORECASE,
    )

    if gender == "f" and re.match(r"^die\s+kunden\b", t, flags=re.IGNORECASE):
        t = re.sub(r"^die\s+kunden\b", "Die Kundin", t, flags=re.IGNORECASE)
    elif gender == "f" and re.match(r"^die\s+kundin\b", t, flags=re.IGNORECASE):
        t = "Die Kundin" + t[len("die Kundin") :]
    elif gender == "m" and re.match(r"^der\s+kunde\b", t, flags=re.IGNORECASE):
        t = "Der Kunde" + t[len("der Kunde") :]
    elif gender == "n":
        if re.match(r"^die\s+kundin\b", t, flags=re.IGNORECASE):
            t = "Die Kundin" + t[len("die Kundin") :]
        elif re.match(r"^der\s+kunde\b", t, flags=re.IGNORECASE):
            t = "Der Kunde" + t[len("der Kunde") :]

    if gender == "m" and not re.search(r"\bkunde\b", t, flags=re.IGNORECASE):
        if re.match(r"^(?:ist|war)\s+", t, flags=re.IGNORECASE):
            t = "Der Kunde " + t
        elif re.match(r"^er\s+ist\b", t, flags=re.IGNORECASE):
            t = "Der Kunde " + t[3:]
    if gender == "f" and not re.search(r"\bkundin\b", t, flags=re.IGNORECASE):
        if re.match(r"^(?:ist|war)\s+", t, flags=re.IGNORECASE):
            t = "Die Kundin " + t
        elif re.match(r"^sie\s+ist\b", t, flags=re.IGNORECASE):
            t = "Die Kundin " + t[3:]

    t = t.strip()
    if not t:
        return ""
    if t[0].islower():
        t = t[0].upper() + t[1:]
    if not t.endswith("."):
        t += "."
    return t


_COMMUNICATION_MARKERS = re.compile(
    r"\b("
    r"gesprochen|unterhalten|informiert|abgestimmt|abgesprochen|"
    r"rücksprache|ruecksprache|kundengespräch|kundengespraech|gespräch|gespraech|"
    r"vor\s+ort|besprochen|geklärt|geklaert"
    r")\b",
    re.IGNORECASE,
)


def _output_has_communication_context(text: str) -> bool:
    return bool(_COMMUNICATION_MARKERS.search(str(text or "")))


def _communication_prefix_from_raw(raw_text: str, *, gender: str) -> str:
    low = _normalize_customer_probe(raw_text).casefold()
    if re.search(r"\bkundengespräch\s+gehabt\b|\bkundengespraech\s+gehabt\b", low):
        return "Kundengespräch geführt"
    if re.search(r"\bkundengespräch\b|\bkundengespraech\b", low):
        return "Kundengespräch geführt"
    if re.search(r"\bmit\s+der\s+kundin\s+(?:gesprochen|unterhalten)\b", low):
        return "Mit der Kundin gesprochen"
    if re.search(r"\bmit\s+dem\s+kunden?\s+(?:gesprochen|unterhalten)\b", low):
        return "Mit dem Kunden gesprochen"
    if re.search(r"\buns\s+mit\s+der\s+kundin\s+unterhalten\b", low):
        return "Mit der Kundin gesprochen"
    if re.search(r"\bdie\s+kundin\s+unterhalten\b", low):
        return "Mit der Kundin gesprochen"
    if re.search(r"\brücksprache\s+mit\s+kund", low) or re.search(r"\bruecksprache\s+mit\s+kund", low):
        return "Rücksprache mit dem Kunden geführt"
    if re.search(r"\bbauherr(?:in)?\s+(?:kurz\s+)?informiert\b", low):
        return "Bauherr informiert"
    if re.search(r"\bauftraggeber\s+(?:kurz\s+)?informiert\b", low):
        return "Auftraggeber informiert"
    if gender == "f" and re.search(r"\bkundin\b", low) and re.search(r"\b(?:gesprochen|gred)\b", low):
        return "Mit der Kundin gesprochen"
    if gender == "m" and re.search(r"\bkunde\b", low) and re.search(r"\b(?:gesprochen|gred)\b", low):
        return "Mit dem Kunden gesprochen"
    return ""


def _to_dependent_clause(text: str, *, gender: str) -> str:
    t = str(text or "").strip().rstrip(".")
    if not t:
        return ""
    t = re.sub(r"^Die Kundin\b", "sie", t, flags=re.IGNORECASE)
    t = re.sub(r"^Der Kunde\b", "er", t, flags=re.IGNORECASE)
    t = re.sub(r"\bwar\s+sehr\b", "ist sehr", t, flags=re.IGNORECASE)
    t = re.sub(r"\bwar\s+zufrieden\b", "ist zufrieden", t, flags=re.IGNORECASE)
    t = re.sub(r"\bdie\s+kundinnen\b", "die Kundin", t, flags=re.IGNORECASE)
    t = re.sub(r"\bkundinnen\b", "Kundin", t, flags=re.IGNORECASE)
    t = re.sub(r"^Bauherrin\b", "die Bauherrin", t, flags=re.IGNORECASE)
    t = re.sub(r"^Bauherr\b", "der Bauherr", t, flags=re.IGNORECASE)
    if gender == "m" and re.match(r"^er\s+ist\b", t, flags=re.IGNORECASE):
        return t
    if gender == "f" and re.match(r"^sie\s+ist\b", t, flags=re.IGNORECASE):
        return t
    return t


def enrich_thin_customer_talk(extracted: str, raw_text: str, *, gender: str = "n") -> str:
    """Ergänzt zu dünne Isolationen um den Gesprächskontext aus dem Rohtext."""
    out = _normalize_whitespace(extracted)
    if not out or out.casefold() == "keine angabe":
        return out
    out = re.sub(
        r"\bkundengespräch\s+gehabt\b",
        "Kundengespräch geführt",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\bkundengespraech\s+gehabt\b",
        "Kundengespräch geführt",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"^(Kundengespräch geführt)\s+",
        r"\1; ",
        out,
        flags=re.IGNORECASE,
    )
    if _output_has_communication_context(out):
        return out

    prefix = _communication_prefix_from_raw(raw_text, gender=gender)
    if not prefix:
        if re.match(r"^kundengespräch\s+gehabt\b", out, flags=re.IGNORECASE):
            tail = re.sub(r"^kundengespräch\s+gehabt\s*", "", out, flags=re.IGNORECASE).strip(" .,;")
            if tail:
                tail = tail[0].upper() + tail[1:] if tail else tail
                return f"Kundengespräch geführt; {tail}."
            return "Kundengespräch geführt."
        return out

    tail = _to_dependent_clause(out, gender=gender)
    if not tail:
        return f"{prefix}."
    if tail.casefold().startswith(prefix.casefold()):
        return out
    return f"{prefix}; {tail}."


def _cleanup_customer_talk_text(text: str) -> str:
    """Glättet Doppel-Satzzeichen und formuliert Präfix+Inhalt natürlicher."""
    t = _normalize_whitespace(text)
    if not t:
        return t
    t = re.sub(r"\s*;\s*;\s*", ". ", t)
    t = re.sub(r"\s*;\s*", ". ", t)
    t = re.sub(r"\s+\.", ".", t)
    t = re.sub(r"\.{2,}", ".", t)
    m = re.match(
        r"^(Mit der Kundin gesprochen|Mit dem Kunden gesprochen|Mit der Kundin unterhalten|"
        r"Mit dem Kunden unterhalten)\s*\.?\s*(.+)$",
        t,
        flags=re.IGNORECASE,
    )
    if m:
        prefix = m.group(1).strip()
        body = m.group(2).strip(" .,;")
        if body and re.search(
            r"\b(gelobt|zufrieden|weiterempfehl|auftrag|freut|einverstanden|happy|muster|farbe)\b",
            body,
            flags=re.IGNORECASE,
        ):
            if body[0].islower():
                body = body[0].upper() + body[1:]
            return f"{prefix}. {body}." if not body.endswith(".") else f"{prefix}. {body}"
    t = _strip_open_item_leading_noise(t)
    if re.match(r"^er\s+(?:war|ist)\s+einverstanden", t, flags=re.IGNORECASE) and not re.search(
        r"\bkund", t, flags=re.IGNORECASE
    ):
        t = re.sub(r"^er\s+(?:war|ist)\b", "Der Kunde ist", t, flags=re.IGNORECASE)
    if re.match(r"^sie\s+(?:war|ist)\s+einverstanden", t, flags=re.IGNORECASE) and not re.search(
        r"\bkund", t, flags=re.IGNORECASE
    ):
        t = re.sub(r"^sie\s+(?:war|ist)\b", "Die Kundin ist", t, flags=re.IGNORECASE)
    if t and not t.endswith("."):
        t += "."
    return t


def _strip_trailing_work_from_customer(text: str) -> str:
    t = _normalize_whitespace(text)
    if not t or not _is_work_polluted(t):
        return t
    m = re.search(
        r"\b\d+(?:[.,]\d+)?\s*(?:qm|m²|m2|quadratmeter|kubik|m³|m3|lfm|meter)\b",
        t,
        flags=re.IGNORECASE,
    )
    if m and m.start() > 10:
        return t[: m.start()].strip(" .,;:")
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", t) if p.strip()]
    kept = [p for p in parts if _has_customer_marker(p) and not _WORK_POLLUTION.search(p)]
    if kept:
        return " ".join(kept)
    return t


def extract_customer_talk_from_text(raw_text: str) -> str:
    """Rohtext → isoliertes, professionelles Kundengespräch."""
    text = _normalize_customer_probe(raw_text)
    if not text or not _has_customer_marker(text):
        return ""

    fragments: list[str] = []
    for sentence in _split_sentences(text):
        frag = _extract_customer_fragment(sentence)
        if frag:
            fragments.append(frag)

    if not fragments:
        tail = _extract_customer_tail(text)
        if tail:
            fragments.append(tail)

    if not fragments:
        return ""

    gender = _detect_customer_gender([text, *fragments])
    polished = [_polish_customer_clause(f, gender=gender) for f in fragments]
    polished = [p for p in polished if p]
    result = _normalize_whitespace(" ".join(polished))
    return _cleanup_customer_talk_text(
        _strip_trailing_work_from_customer(
            enrich_thin_customer_talk(result, text, gender=gender)
        )
    )


def refine_customer_talk(
    raw_text: str,
    existing: str,
    *,
    summary: str = "",
) -> str:
    """Bereinigt customerTalk: kein Summary-Duplikat, kein Arbeitstext."""
    raw = str(raw_text or "").strip()
    current = _normalize_whitespace(existing)
    summ = _normalize_whitespace(summary)
    gender = _detect_customer_gender([raw, current])

    def _finalize(value: str) -> str:
        v = _normalize_whitespace(value)
        if not v or v.casefold() == "keine angabe":
            return v
        v = enrich_thin_customer_talk(v, raw, gender=_detect_customer_gender([raw, v]))
        return _cleanup_customer_talk_text(_strip_trailing_work_from_customer(v))

    if current.casefold() in {"keine angabe", ""}:
        extracted = extract_customer_talk_from_text(raw)
        return _finalize(extracted or current)

    if summ and current.casefold() == summ.casefold():
        extracted = extract_customer_talk_from_text(raw)
        return _finalize(extracted or current)

    if _is_work_polluted(current) or (summ and summ.casefold() in current.casefold()):
        extracted = extract_customer_talk_from_text(raw)
        if extracted:
            return _finalize(extracted)
        return ""

    if _has_customer_marker(current) and not _is_work_polluted(current):
        polished = _polish_customer_clause(current, gender=gender)
        if polished:
            return _finalize(polished)

    extracted = extract_customer_talk_from_text(raw)
    if extracted:
        return _finalize(extracted)
    if _is_work_polluted(current):
        return ""
    return _finalize(current)
