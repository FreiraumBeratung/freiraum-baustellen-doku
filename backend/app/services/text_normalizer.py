from __future__ import annotations

import re
from typing import Any

from app.services.trade_profiles import TRADE_PROFILES

_UNIVERSAL_NORMALIZATION: dict[str, str] = {
    "qm": "m²",
    "quadratmeter": "m²",
    "kubikmeter": "m³",
    "tonnen": "t",
    "split": "Splitt",
    "2 5 split": "Splitt 2/5 mm",
    "2/5 split": "Splitt 2/5 mm",
    "zwei fünfer split": "Splitt 2/5 mm",
    "zwei fuenfer split": "Splitt 2/5 mm",
    "zwei fünfer splitt": "Splitt 2/5 mm",
    "zwei fuenfer splitt": "Splitt 2/5 mm",
    "zwei fünf split": "Splitt 2/5 mm",
    "zwei fuenf split": "Splitt 2/5 mm",
    "zwei-fünfer split": "Splitt 2/5 mm",
    "zwei-fuenfer split": "Splitt 2/5 mm",
}

_ACTIVITY_MATERIAL_RULES: dict[str, list[str]] = {
    "pflaster verlegt": ["Pflastersteine", "Splitt", "Schotter"],
    "schotter eingebaut": ["Schotter"],
    "pflanzsubstrat eingebracht": ["Pflanzsubstrat"],
    "pflanzkübel mit pflanzsubstrat verfüllt": ["Pflanzsubstrat"],
    "gipskartonplatten montiert": ["Gipskartonplatten", "Schnellbauschrauben"],
    "trockenbauwand geschlossen": ["Gipskartonplatten", "Spachtelmasse"],
    "verspachtelungsarbeiten durchgeführt": ["Spachtelmasse"],
    "fliesen verlegt": ["Fliesen", "Fliesenkleber", "Fugenmörtel"],
    "fliesenarbeiten durchgeführt": ["Fliesen", "Fliesenkleber", "Fugenmörtel"],
    "rohrleitungen installiert": ["Rohrleitungen", "Fittings", "Befestigungsmaterial"],
    "heizungsanlage montiert": ["Rohrleitungen", "Fittings"],
    "heizungsanschlüsse hergestellt": ["Rohrleitungen", "Fittings"],
    "trinkwasseranschlüsse hergestellt": ["Rohrleitungen", "Fittings"],
    "leitungen verlegt": ["Elektroleitungen", "Installationsmaterial"],
    "sanierputz aufgetragen": ["Sanierputz", "Grundierung"],
    "aufbringung von sanierputz": ["Sanierputz", "Grundierung"],
    "gipskarton montiert": ["Gipskartonplatten", "Schnellbauschrauben", "Spachtelmasse"],
    "herstellung von silikonfugen": ["Silikon"],
    "montage der wasserleitungen": ["Rohrleitungen", "Fittings"],
}


def _replace_phrase(text: str, source: str, target: str) -> str:
    escaped = [re.escape(x) for x in source.split()]
    pattern = r"\b" + r"\s+".join(escaped) + r"\b"
    return re.sub(pattern, target, text, flags=re.IGNORECASE)


def _collect_normalizations() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = list(_UNIVERSAL_NORMALIZATION.items())
    for profile in TRADE_PROFILES.values():
        mapping = profile.get("normalization")
        if not isinstance(mapping, dict):
            continue
        for src, dst in mapping.items():
            left = str(src or "").strip()
            right = str(dst or "").strip()
            if left and right:
                pairs.append((left, right))
    pairs.sort(key=lambda it: len(it[0]), reverse=True)
    return pairs


def normalize_text(raw_text: str) -> str:
    text = str(raw_text or "").strip()
    if not text:
        return ""
    out = text
    for source, target in _collect_normalizations():
        out = _replace_phrase(out, source, target)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def detect_trades(text: str) -> list[str]:
    probe = normalize_text(text).casefold()
    hits: list[str] = []
    for name, profile in TRADE_PROFILES.items():
        keywords = profile.get("keywords")
        if not isinstance(keywords, list):
            continue
        for kw in keywords:
            needle = str(kw or "").strip().casefold()
            if needle and re.search(r"\b" + re.escape(needle) + r"\b", probe):
                hits.append(name)
                break
    return sorted(set(hits))


def collect_activity_hints(text: str) -> list[str]:
    probe = normalize_text(text).casefold()
    out: list[str] = []
    for profile in TRADE_PROFILES.values():
        phrases = profile.get("phrases")
        if not isinstance(phrases, list):
            continue
        for phrase in phrases:
            val = str(phrase or "").strip()
            if not val:
                continue
            if re.search(r"\b" + re.escape(val.casefold()) + r"\b", probe):
                out.append(val)
    return _dedupe(out)


def infer_materials_from_activities(activities: list[str], raw_text: str = "") -> list[str]:
    acts = [str(a or "").strip() for a in activities if str(a or "").strip()]
    act_probe = " | ".join(acts).casefold()
    text_probe = normalize_text(raw_text).casefold()
    out: list[str] = []

    for trigger, materials in _ACTIVITY_MATERIAL_RULES.items():
        trig = trigger.casefold()
        if trig in act_probe or trig in text_probe:
            out.extend(materials)

    # Nur explizit im Rohtext erwähnte zusätzliche Materialien aus Profilen ergänzen.
    for profile in TRADE_PROFILES.values():
        materials = [str(m or "").strip() for m in profile.get("materials", []) if str(m or "").strip()]
        for material in materials:
            if material.casefold() in text_probe:
                out.append(material)
    return _dedupe(out)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        val = str(raw or "").strip()
        if not val:
            continue
        key = val.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(val)
    return out


def build_summary(input_data: dict[str, Any], activities: list[str]) -> str:
    acts = _dedupe([str(a or "").strip() for a in activities if str(a or "").strip()])
    if not acts:
        return "Keine Angabe"

    date_text = _format_date_de(str(input_data.get("date") or "").strip())
    project = str(input_data.get("projectName") or "").strip()
    date_label = f"Am {date_text} " if date_text and date_text != "Keine Angabe" else ""
    site_label = f"auf der Baustelle {project}" if project else "auf der Baustelle"

    if len(acts) == 1:
        return f"{date_label}wurden {site_label} {acts[0]}.".strip()
    if len(acts) == 2:
        return f"{date_label}wurden {site_label} {acts[0]} sowie {acts[1]}.".strip()

    return f"{date_label}wurden {site_label} {acts[0]}, {acts[1]} sowie {acts[2]}.".strip()


def _format_date_de(value: str) -> str:
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", value)
    if not m:
        return value
    return f"{m.group(3)}.{m.group(2)}.{m.group(1)}"
