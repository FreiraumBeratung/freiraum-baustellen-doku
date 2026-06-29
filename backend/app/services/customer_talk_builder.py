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
    r"kundengespräch|kundengespraech|"
    r"die\s+kundin|der\s+kunde|die\s+kunden|dem\s+kunden|"
    r"bauherr\s+war|bauherrin\s+war|bauleitung\s+war"
    r")",
    re.IGNORECASE,
)

_WORK_POLLUTION = re.compile(
    r"\b("
    r"gelegt|verlegt|montiert|eingebaut|gebaut|gemacht|gegossen|geschalt|"
    r"pflaster|fliesen|beton|schotter|mauerwerk|schalung|bewehrung|"
    r"erdarbeiten|graben|heizkörper|heizkoerper|wc|putz|trockenbau"
    r")\b|"
    r"\d+(?:[.,]\d+)?\s*(?:qm|m²|m2|quadratmeter|kubik|m³|m3|lfm|meter)\b",
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
    r"\s+(?=(?:anschließend|anschliessend|danach|dann|im\s+anschluss|hinterher|später|spaeter)\b)",
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


def _split_sentences(text: str) -> list[str]:
    t = _TRANSITION_SPLIT.sub(". ", str(text or "").strip())
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", t) if p.strip()]
    if parts:
        return parts
    # Run-on ohne Satzzeichen: an Problem/Offen/Kundenhinweis splitten.
    chunks = [c.strip() for c in _PROBLEM_OPEN_SPLIT.split(t) if c.strip()]
    if len(chunks) > 1:
        return chunks
    return [t] if t else []


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
    return _normalize_whitespace(" ".join(polished))


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

    if current.casefold() in {"keine angabe", ""}:
        extracted = extract_customer_talk_from_text(raw)
        return extracted or current

    if summ and current.casefold() == summ.casefold():
        extracted = extract_customer_talk_from_text(raw)
        return extracted or current

    if _is_work_polluted(current) or (summ and summ.casefold() in current.casefold()):
        extracted = extract_customer_talk_from_text(raw)
        if extracted:
            return extracted
        return ""

    if _has_customer_marker(current) and not _is_work_polluted(current):
        gender = _detect_customer_gender([raw, current])
        polished = _polish_customer_clause(current, gender=gender)
        if polished:
            return polished

    extracted = extract_customer_talk_from_text(raw)
    if extracted:
        return extracted
    if _is_work_polluted(current):
        return ""
    return current
