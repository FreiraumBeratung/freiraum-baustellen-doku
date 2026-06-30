"""Summary-Guards: keine Material-Wiederholung, wenn Materialien im Material-Reiter stehen.

Rein additiv — wird nach deterministischer Summary und nach KI-Polish angewendet.
"""

from __future__ import annotations

import re

_MATERIAL_ECHO_PHRASES = re.compile(
    r"\b(?:dafür|dafuer|hierbei|dabei|dadurch|außerdem|ausserdem|zusätzlich|zusaetzlich)\s+kam(?:en)?\b"
    r"|\bzum\s+einsatz\b",
    flags=re.IGNORECASE,
)

_MATERIAL_ECHO_VERBS = re.compile(
    r"\b(?:verarbeitet|verbaut|verwendet|eingesetzt|eingebaut|reingemacht|reingepackt)\b|zum\s+einsatz\b",
    flags=re.IGNORECASE,
)


def _material_key(value: str) -> str:
    t = str(value or "").casefold().strip()
    if not t:
        return ""
    t = re.sub(
        r"\b(benutzt|verwendet|verarbeitet|eingebaut|aufgetragen|aufgebracht|montiert|gesetzt|verlegt)\b",
        " ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"[^a-z0-9äöüß/\s-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\bpflaster\s+steine?\b", "pflastersteine", t)
    t = re.sub(r"\bfliesen\s+kleber\b", "fliesenkleber", t)
    return t


def _material_in_sentence(material: str, sentence_low: str) -> bool:
    m = str(material or "").casefold().strip()
    if not m:
        return False
    if m in sentence_low:
        return True
    key = _material_key(m)
    if not key:
        return False
    sent_key = _material_key(sentence_low)
    return bool(key and (key in sent_key or sent_key in key))


def _sentence_reflects_activity(sentence: str, activities: list[str]) -> bool:
    """True, wenn der Satz eine echte Tätigkeit aus der Liste wiedergibt."""
    low = str(sentence or "").casefold().strip()
    if not low:
        return False
    action_verbs = (
        "verlegt",
        "eingebaut",
        "gesetzt",
        "montiert",
        "verarbeitet",
        "aufgetragen",
        "aufgebracht",
        "geschlossen",
        "erstellt",
        "gestellt",
        "verdichtet",
        "geschnitten",
        "entfernt",
        "verfugt",
    )
    for act in activities:
        a = str(act).casefold().strip()
        if not a:
            continue
        if a in low:
            return True
        act_key = _material_key(a)
        if not act_key or len(act_key) < 4:
            continue
        sent_key = _material_key(low)
        if act_key not in sent_key and not sent_key.startswith(act_key):
            continue
        if any(v in a and v in low for v in action_verbs):
            return True
    return False


def _sentence_is_material_echo(sentence: str, materials: list[str], activities: list[str]) -> bool:
    low = str(sentence or "").casefold().strip()
    if not low or not materials:
        return False
    if _sentence_reflects_activity(sentence, activities):
        return False
    acts_joined = " ".join(str(a) for a in activities).casefold()

    if _MATERIAL_ECHO_PHRASES.search(low):
        if "zum einsatz" in low:
            return True
        if any(_material_in_sentence(m, low) for m in materials):
            return True

    if "zum einsatz" in low:
        return True

    if not _MATERIAL_ECHO_VERBS.search(low):
        return False

    for mat in materials:
        m = str(mat).casefold().strip()
        if not m or not _material_in_sentence(m, low):
            continue
        if "pflasterstein" in m and "pflaster" in acts_joined:
            return True
        if "fliesen" in m and "fliesen verlegt" in acts_joined:
            return True
        if "putz" in m and "putz" in acts_joined and "verputzt" in acts_joined:
            return True
        mat_key = _material_key(m)
        rem = _MATERIAL_ECHO_VERBS.sub(" ", low)
        rem = re.sub(r"\b(dafür|dafuer|kamen|kam|zu|dem|der|die|das|es|sie|hierbei|dabei)\b", " ", rem)
        rem = re.sub(r"\s+", " ", rem).strip()
        rem_key = _material_key(rem)
        if mat_key and (mat_key == rem_key or mat_key in rem_key):
            return True
    return False


def summary_has_material_echo(summary: str, materials: list[str], activities: list[str]) -> bool:
    mats = [str(m).strip() for m in (materials or []) if str(m).strip()]
    if not mats:
        return False
    text = str(summary or "").strip()
    if not text:
        return False
    for sent in _split_summary_sentences(text):
        if _sentence_is_material_echo(sent, mats, activities or []):
            return True
    return False


def detect_material_echo_in_summary(
    summary: str, materials: list[str], activities: list[str]
) -> str | None:
    """Wie in Wave-20-Smokes: liefert einen kurzen Grund-String oder None."""
    mats = [str(m).strip() for m in (materials or []) if str(m).strip()]
    if not mats:
        return None
    low = str(summary or "").casefold()
    acts_joined = " ".join(str(a) for a in (activities or [])).casefold()
    for mat in mats:
        m = mat.casefold()
        if not m or m not in low:
            continue
        if not _MATERIAL_ECHO_VERBS.search(low) and not _MATERIAL_ECHO_PHRASES.search(low):
            continue
        if "pflasterstein" in m and "pflaster" in acts_joined and "pflasterstein" in low:
            return "Material-Echo Pflaster/Pflastersteine in Summary"
        if "fliesen verlegt" in acts_joined and "fliesen" in m and "fliesen" in low:
            return "Material-Echo Fliesen in Summary"
    if re.search(r"\bdaf(ü|ue)r\s+kam", low) and any(
        "pflasterstein" in str(x).casefold() for x in mats
    ):
        return "dafür kamen … zum Einsatz in Summary"
    if "zum einsatz" in low and mats:
        return "zum Einsatz in Summary"
    return None


def _split_summary_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", str(text or "").strip())
    return [p.strip() for p in parts if p.strip()]


def strip_material_echo_from_summary(
    summary: str, materials: list[str], activities: list[str]
) -> str:
    """Entfernt Material-Echo-Sätze; belässt Tätigkeits-Sätze."""
    text = str(summary or "").strip()
    mats = [str(m).strip() for m in (materials or []) if str(m).strip()]
    if not text or not mats:
        return text

    sentences = _split_summary_sentences(text)
    if not sentences:
        return text

    kept = [s for s in sentences if not _sentence_is_material_echo(s, mats, activities or [])]
    if kept:
        return " ".join(kept).strip()

    # Fallback: letzten Satz verwerfen, wenn er Echo ist (typisch KI-Polish).
    if len(sentences) > 1 and _sentence_is_material_echo(sentences[-1], mats, activities or []):
        return " ".join(sentences[:-1]).strip()

    return text
