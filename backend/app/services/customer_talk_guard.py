"""Guards für KI-Polish des Kundengesprächs — rein additiv."""

from __future__ import annotations

import re

from app.services.customer_talk_builder import _has_customer_marker, _is_work_polluted


def _sentence_count(text: str) -> int:
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", str(text or "").strip()) if p.strip()]
    return len(parts) if parts else (1 if str(text or "").strip() else 0)


def customer_talk_polish_is_safe(
    polished: str,
    deterministic: str,
    *,
    raw_text: str = "",
    summary: str = "",
) -> bool:
    t = str(polished or "").strip()
    det = str(deterministic or "").strip()
    if len(t) < 12 or len(t) > 650:
        return False
    if "{" in t or "}" in t or "[" in t:
        return False
    if _sentence_count(t) > 2:
        return False
    if _is_work_polluted(t):
        return False
    if not _has_customer_marker(t):
        return False
    summ = str(summary or "").strip()
    if summ and t.casefold() == summ.casefold():
        return False

    allowed_src = " ".join([det, raw_text, summary])
    allowed = set(re.findall(r"\d+", allowed_src))
    found = set(re.findall(r"\d+", t))
    if found - allowed:
        return False

    det_low = det.casefold()
    t_low = t.casefold()

    def _has_word(hay: str, word: str) -> bool:
        return bool(re.search(rf"\b{re.escape(word)}\b", hay))

    preserve_tokens = (
        "auftrag",
        "auftraege",
        "einverstanden",
        "informiert",
        "abgestimmt",
        "abgesprochen",
        "muster",
        "farbe",
        "happy",
        "meckert",
        "beschwert",
        "reklam",
        "gelobt",
        "weiterempfehl",
        "kollegen",
        "freunden",
        "freut",
    )
    for token in preserve_tokens:
        if _has_word(det_low, token) and not _has_word(t_low, token):
            return False
    if _has_word(det_low, "zufrieden") and not _has_word(t_low, "zufrieden"):
        return False

    if re.search(r"\bkundin\b", det_low) and not re.search(r"\bkundin\b", t_low):
        return False
    if re.search(r"\bkunde\b", det_low) and not re.search(r"\bkunde\b", t_low):
        return False
    if re.search(r"\bbauherr", det_low) and not re.search(r"\bbauherr", t_low):
        return False
    if re.search(r"\bauftraggeber\b", det_low) and not re.search(r"\bauftraggeber\b", t_low):
        return False

    return True


def strip_work_pollution_from_customer_talk(text: str) -> str:
    """Letzte Sicherheitsschicht — entfernt Arbeitstext-Artefakte."""
    t = str(text or "").strip()
    if not t or not _is_work_polluted(t):
        return t
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", t) if p.strip()]
    kept = [p for p in parts if not _is_work_polluted(p)]
    if kept:
        return " ".join(kept).strip()
    return ""
