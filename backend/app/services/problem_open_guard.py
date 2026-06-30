"""Guards für KI-Polish von Problemen und offenen Punkten — rein additiv."""

from __future__ import annotations

import re

from app.services.problem_open_builder import (
    _has_customer_marker,
    _has_open_substance,
    _has_problem_substance,
    _is_work_polluted,
)


def _sentence_count(text: str) -> int:
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", str(text or "").strip()) if p.strip()]
    return len(parts) if parts else (1 if str(text or "").strip() else 0)


def _has_word(hay: str, word: str) -> bool:
    return bool(re.search(rf"\b{re.escape(word)}\b", hay))


def problem_item_polish_is_safe(
    polished: str,
    deterministic: str,
    *,
    raw_text: str = "",
) -> bool:
    t = str(polished or "").strip()
    det = str(deterministic or "").strip()
    if len(t) < 6 or len(t) > 260:
        return False
    if "{" in t or "}" in t or "[" in t:
        return False
    if _sentence_count(t) > 2:
        return False
    if _is_work_polluted(t):
        return False
    if _has_customer_marker(t):
        return False
    if not _has_problem_substance(t):
        return False

    allowed_src = " ".join([det, raw_text])
    allowed = set(re.findall(r"\d+", allowed_src))
    found = set(re.findall(r"\d+", t))
    if found - allowed:
        return False

    det_low = det.casefold()
    t_low = t.casefold()
    preserve_tokens = (
        "lieferung",
        "regen",
        "drainage",
        "verzöger",
        "verzoeger",
        "defekt",
        "kaputt",
        "fehlt",
        "wasserdruck",
        "armatur",
        "material",
        "spät",
        "spaet",
    )
    for token in preserve_tokens:
        if _has_word(det_low, token) and not _has_word(t_low, token):
            return False
    return True


def open_item_polish_is_safe(
    polished: str,
    deterministic: str,
    *,
    raw_text: str = "",
) -> bool:
    t = str(polished or "").strip()
    det = str(deterministic or "").strip()
    if len(t) < 6 or len(t) > 260:
        return False
    if "{" in t or "}" in t or "[" in t:
        return False
    if _sentence_count(t) > 2:
        return False
    if _is_work_polluted(t):
        return False
    if _has_customer_marker(t):
        return False
    if not _has_open_substance(t) and not re.search(r"\boffen\b", t, flags=re.IGNORECASE):
        return False

    allowed_src = " ".join([det, raw_text])
    allowed = set(re.findall(r"\d+", allowed_src))
    found = set(re.findall(r"\d+", t))
    if found - allowed:
        return False

    det_low = det.casefold()
    t_low = t.casefold()
    preserve_tokens = (
        "morgen",
        "montag",
        "woche",
        "rest",
        "reihe",
        "armatur",
        "nachliefer",
        "nachbestell",
    )
    for token in preserve_tokens:
        if _has_word(det_low, token) and not _has_word(t_low, token):
            return False
    return True


def strip_pollution_from_problem_open_item(text: str) -> str:
    t = str(text or "").strip()
    if not t:
        return ""
    if not _is_work_polluted(t) and not _has_customer_marker(t):
        return t
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", t) if p.strip()]
    kept = [p for p in parts if not _is_work_polluted(p) and not _has_customer_marker(p)]
    return " ".join(kept).strip()
