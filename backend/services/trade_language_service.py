from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.services.text_normalizer import (
    build_summary,
    collect_activity_hints,
    detect_trades,
    infer_materials_from_activities as infer_materials_from_profiles,
    normalize_text,
)

BASE_DIR = Path(__file__).resolve().parents[1]
TRADE_DICTIONARY_FILE = BASE_DIR / "config" / "trade_dictionary.json"


@lru_cache(maxsize=1)
def _load_trade_dictionary() -> dict[str, Any]:
    if not TRADE_DICTIONARY_FILE.exists():
        return {}
    with TRADE_DICTIONARY_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _dedupe_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        v = str(raw or "").strip()
        if not v:
            continue
        key = v.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


_MAIN_ACTIVITY_KEYWORDS = (
    "verlegt",
    "montiert",
    "installiert",
    "eingebaut",
    "geschlossen",
    "aufbringung",
    "aufgetragen",
    "erstellt",
    "hergestellt",
)

_SECONDARY_ACTIVITY_KEYWORDS = (
    "silikonfugen",
    "nachgespachtelt",
    "nacharbeit",
    "nacharbeiten",
    "gereinigt",
    "kontrolliert",
    "abnahme",
)


def _clean_activity_value(value: str) -> str:
    t = str(value or "").strip()
    if not t:
        return ""
    t = re.sub(r"^(wir haben heute|wir haben|heute haben wir)\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^(danach|anschließend|anschliessend|zum schluss|zum schluß)\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^(die|der|das)\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip(" ,.;")
    return t


def _expand_activity_fragments(value: str) -> list[str]:
    base = _clean_activity_value(value)
    if not base:
        return []
    parts = [p.strip(" ,.;") for p in re.split(r"\s*,\s*|\s+und\s+|\s+sowie\s+", base, flags=re.IGNORECASE)]
    parts = [p for p in parts if p]
    if len(parts) <= 1:
        return [base]
    expanded: list[str] = []
    for p in parts:
        lp = p.casefold()
        if _has_quantity(p) or any(k in lp for k in _MAIN_ACTIVITY_KEYWORDS) or "silikonfugen" in lp:
            expanded.append(p)
    return expanded if expanded else [base]


def _has_quantity(text: str) -> bool:
    t = text.casefold()
    return bool(
        re.search(r"\b\d+(?:[.,]\d+)?\s*(m²|m2|qm|m³|m3|t|kg|mm|cm)\b", t)
        or re.search(r"\b\d+(?:[.,]\d+)?\b", t)
    )


def _normalize_for_similarity(text: str) -> str:
    t = normalize_text(text).casefold()
    t = re.sub(r"\bverlegung von\b", "verlegt", t)
    t = re.sub(r"\bentfernung des alten putzes\b", "altputz entfernt", t)
    t = re.sub(r"\bentfernung von altputz\b", "altputz entfernt", t)
    t = re.sub(r"\bdurchführung von\b", "", t)
    t = re.sub(r"\bherstellung von\b", "", t)
    t = re.sub(r"\bmontage von\b", "montage", t)
    t = re.sub(r"\b\d+(?:[.,]\d+)?\s*(m²|m2|qm|m³|m3|t|kg|mm|cm)\b", " ", t)
    t = re.sub(r"\b\d+(?:[.,]\d+)?\b", " ", t)
    t = re.sub(r"[^a-z0-9äöüß/\s-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _activity_similarity(a: str, b: str) -> float:
    na = _normalize_for_similarity(a)
    nb = _normalize_for_similarity(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    sa = set(na.split())
    sb = set(nb.split())
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    if union == 0:
        return 0.0
    return inter / union


def _priority_score(activity: str) -> float:
    t = activity.casefold()
    score = 0.0
    if _has_quantity(activity):
        score += 6.0
    if any(k in t for k in _MAIN_ACTIVITY_KEYWORDS):
        score += 3.0
    if any(k in t for k in _SECONDARY_ACTIVITY_KEYWORDS):
        score -= 2.0
    if re.search(r"\b(wir|ich|heute|danach|anschließend|anschliessend)\b", t):
        score -= 3.5
    if "," in activity:
        score -= 2.0
    if len(activity.split()) > 10:
        score -= 1.5
    if "fliesen verlegt" in t or "pflaster verlegt" in t or "trockenbauwand geschlossen" in t:
        score += 2.0
    score += min(len(activity), 120) / 150.0
    return score


def _prefer_better_activity(a: str, b: str) -> str:
    sa = _priority_score(a)
    sb = _priority_score(b)
    if sb > sa:
        return b
    if sb == sa and len(b) > len(a):
        return b
    return a


def _semantic_dedupe_activities(values: list[str]) -> list[str]:
    expanded: list[str] = []
    for v in values:
        expanded.extend(_expand_activity_fragments(v))
    candidates = _dedupe_preserve([v for v in expanded if v])
    chosen: list[str] = []
    for cand in candidates:
        replaced = False
        for idx, existing in enumerate(chosen):
            sim = _activity_similarity(cand, existing)
            if sim >= 0.72:
                chosen[idx] = _prefer_better_activity(existing, cand)
                replaced = True
                break
            # "enthalten"-Regel für sehr nahe Varianten mit identischem Kern.
            n_c = _normalize_for_similarity(cand)
            n_e = _normalize_for_similarity(existing)
            if n_c and n_e and (n_c in n_e or n_e in n_c):
                chosen[idx] = _prefer_better_activity(existing, cand)
                replaced = True
                break
        if not replaced:
            chosen.append(cand)
    # Wichtigste Tätigkeiten zuerst.
    chosen.sort(key=_priority_score, reverse=True)
    return chosen


def _prefer_specific_phrases(values: list[str]) -> list[str]:
    items = _dedupe_preserve(values)
    # Präzisere Varianten behalten: "50 m² Pflaster verlegt" soll "Pflaster verlegt" verdrängen.
    result: list[str] = []
    for candidate in sorted(items, key=len, reverse=True):
        cand_key = candidate.casefold()
        if any(cand_key in existing.casefold() and cand_key != existing.casefold() for existing in result):
            continue
        result.append(candidate)
    return list(reversed(result))


def _compact_activity_items(values: list[str]) -> list[str]:
    vals = _semantic_dedupe_activities(values)
    concise = [v for v in vals if "," not in v and len(v.split()) <= 8]
    if concise:
        concise.sort(key=_priority_score, reverse=True)
        return concise
    return vals


def _clean_material_value(value: str) -> str:
    v = str(value or "").strip()
    if not v:
        return ""
    if "," in v or re.search(r"\b(haben wir|wir haben|heute haben)\b", v.casefold()):
        return ""
    v = re.sub(r"^(danach|anschließend|anschliessend|zum schluss|zum schluß)\s+", "", v, flags=re.IGNORECASE)
    # Tätigkeitssuffixe auf Material kürzen, z. B. "Splitt 2/5 mm eingebaut" -> "Splitt 2/5 mm"
    v = re.sub(
        r"\s+(eingebaut|verlegt|montiert|installiert|durchgeführt|hergestellt|vorbereitet|verfüllt|eingebracht)$",
        "",
        v,
        flags=re.IGNORECASE,
    ).strip()
    if len(v.split()) > 6:
        return ""
    return v


def _material_terms_from_dictionary() -> list[str]:
    trade_dict = _load_trade_dictionary()
    found: list[str] = []
    for section in trade_dict.values():
        if not isinstance(section, dict):
            continue
        terms = section.get("material_terms")
        if not isinstance(terms, list):
            continue
        for term in terms:
            txt = str(term or "").strip()
            if txt:
                found.append(txt)
    return _dedupe_preserve(found)


def normalize_trade_language(text: str) -> str:
    return normalize_text(text)


def extract_material_hints(text: str) -> list[str]:
    probe = normalize_trade_language(text).casefold()
    found: list[str] = []
    for term in _material_terms_from_dictionary():
        if re.search(r"\b" + re.escape(term.casefold()) + r"\b", probe):
            found.append(term[0].upper() + term[1:] if len(term) > 1 else term)
    cleaned = [_clean_material_value(x) for x in found]
    return _prefer_specific_phrases([x for x in cleaned if x])


def extract_activity_hints(text: str) -> list[str]:
    hints = collect_activity_hints(text)
    return _prefer_specific_phrases(hints)


def infer_materials_from_activities(activities: list[str]) -> list[str]:
    from_profiles = infer_materials_from_profiles(activities)
    from_dictionary: list[str] = []
    trade_dict = _load_trade_dictionary()
    folded_activities = [str(a or "").strip().casefold() for a in activities if str(a or "").strip()]

    for section in trade_dict.values():
        if not isinstance(section, dict):
            continue
        mapping = section.get("material_inference")
        if not isinstance(mapping, dict):
            continue
        for trigger, materials in mapping.items():
            trigger_norm = str(trigger or "").strip().casefold()
            if not trigger_norm or not isinstance(materials, list):
                continue
            if any(trigger_norm in act for act in folded_activities):
                from_dictionary.extend(str(m or "").strip() for m in materials if str(m or "").strip())
    cleaned = [_clean_material_value(x) for x in (from_profiles + from_dictionary)]
    return _prefer_specific_phrases([x for x in cleaned if x])


def build_professional_summary(input_data: dict[str, Any], structured: dict[str, Any]) -> str:
    activities = [str(x).strip() for x in (structured.get("activities") or []) if str(x).strip()]
    activities = _compact_activity_items(activities)
    if not activities:
        return "Keine Angabe"
    summary = build_summary(input_data, activities)
    trades = detect_trades(" ".join(activities))
    if trades and summary.endswith("."):
        return summary
    return summary


def dedupe_specific_activities(values: list[str]) -> list[str]:
    return _compact_activity_items(values)


def dedupe_specific_materials(values: list[str]) -> list[str]:
    cleaned = [_clean_material_value(x) for x in values]
    return _dedupe_preserve([x for x in cleaned if x])
