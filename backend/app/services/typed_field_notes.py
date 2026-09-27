"""Rettung getippter Feldnotizen — nur wenn die Engine nichts erkannt hat.

Sprache, Stichpunkt-Listen und der Quality-Filter bleiben unberührt.
Kein Raten, kein Kundengespräch, kein Material erfinden.
"""

from __future__ import annotations

import re

_MIN_CHARS = 8
_MIN_CHUNK = 6
_MAX_RAW = 400
_MAX_CHUNK = 180

_NOISE = re.compile(
    r"^(test|asdf|xxx+|aaa+|123+|keine\s*angabe|\.+|\?+)$",
    re.IGNORECASE,
)

_SPEECH_MARKERS = re.compile(
    r"\b("
    r"heute\s+haben\s+wir|wir\s+haben\s+heute|also\s+wir|"
    r"dann\s+haben\s+wir|ich\s+habe\s+heute|"
    r"der\s+kunde\s+(sagte|hat|meinte)|kundin\s+(sagte|hat|meinte)"
    r")\b",
    re.IGNORECASE,
)

_FUTURE = re.compile(
    r"\b(morgen|nächste\s+woche|naechste\s+woche|übermorgen|uebermorgen)\b",
    re.IGNORECASE,
)

_EFFORT_PREFIX = re.compile(
    r"^(?:zusatzaufwand(?:\s+zum\s+lv+)?)\s*:\s*",
    re.IGNORECASE,
)


def _clean_line(value: str) -> str:
    s = str(value or "").strip(" \t-•")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _has_letter(value: str) -> bool:
    return bool(re.search(r"[A-Za-zÄÖÜäöüß]", value))


def _has_work_substance(raw: str) -> bool:
    s = _clean_line(raw)
    if len(s) < _MIN_CHARS or not _has_letter(s):
        return False
    return not bool(_NOISE.match(s))


def looks_like_typed_field_note(raw_text: str) -> bool:
    s = str(raw_text or "").strip()
    if not _has_work_substance(s):
        return False
    if len(s) > _MAX_RAW:
        return False
    if _SPEECH_MARKERS.search(s):
        return False
    if _FUTURE.search(s):
        return False
    return True


def _strip_effort_prefix(value: str) -> str:
    s = _clean_line(value)
    return _EFFORT_PREFIX.sub("", s).strip()


def _finish(value: str) -> str:
    s = _clean_line(value)
    if not s:
        return ""
    if len(s) > _MAX_CHUNK:
        s = s[:_MAX_CHUNK].rstrip(" .,;:")
    if s and s[-1] not in ".!?":
        s = f"{s}."
    return s


def _split_chunks(raw: str) -> list[str]:
    parts = re.split(r"[\n;]+|(?<=[.!?])\s+", str(raw or ""))
    out: list[str] = []
    seen: set[str] = set()
    for part in parts:
        chunk = _finish(_strip_effort_prefix(part))
        if not chunk or len(chunk) < _MIN_CHUNK:
            continue
        if not _has_letter(chunk) or _NOISE.match(chunk.rstrip(".")):
            continue
        key = chunk.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(chunk)
    return out


def rescue_typed_field_notes(raw_text: str, existing_activities: list[str] | None = None) -> list[str]:
    """Liefert Tätigkeiten aus dem Rohtext — leer, wenn schon welche da sind oder kein Notiz-Fall."""
    existing = [str(x).strip() for x in (existing_activities or []) if str(x).strip()]
    if existing:
        return []
    raw = str(raw_text or "").strip()
    if not looks_like_typed_field_note(raw):
        return []
    chunks = _split_chunks(raw)
    if chunks:
        return chunks
    finished = _finish(_strip_effort_prefix(raw))
    return [finished] if finished else []
