from __future__ import annotations

import re


_HUMAN_ACTIVITY_RULES: tuple[tuple[str, str], ...] = (
    (r"\bdurchführung von spachtelarbeiten\b", "Spachtelarbeiten durchgeführt"),
    (r"\bdurchführung von verfugungsarbeiten\b", "Fliesen verfugt"),
    (r"\bverarbeitung von (\d+(?:[.,]\d+)?\s*m³)\s*schotter\b", r"\1 Schotter eingebaut"),
    (r"\beinbau von (\d+(?:[.,]\d+)?\s*m³)\s*schotter\b", r"\1 Schotter eingebaut"),
    (r"\bverlegung von\s*(ca\.\s*)?(\d+(?:[.,]\d+)?\s*m²)\s*fliesen\b", r"ca. \2 Fliesen verlegt"),
    (r"\bfliesenverlegung im bad\b", "Im Bad Fliesen verlegt"),
    (r"\bfertigstellung der pflanzkübel\b", "Pflanzkübel mit Erde befüllt"),
    (r"\bherstellung von silikonfugen\b", "Silikonfugen hergestellt"),
    (r"\bmontage von wasserleitungen\b", "Wasserleitungen montiert"),
    (r"\bheizungsanschlüsse hergestellt\b", "Heizungsanschlüsse montiert"),
    (r"\bdurchführung von\b", ""),
)


def humanize_activity(text: str) -> str:
    out = str(text or "").strip()
    if not out:
        return ""
    for pattern, repl in _HUMAN_ACTIVITY_RULES:
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)
    out = re.sub(r"\s+", " ", out).strip(" ,.;")
    return out


def humanize_material(text: str) -> str:
    t = str(text or "").strip()
    if not t:
        return ""
    l = t.casefold()

    if "pflaster" in l:
        return "Pflastersteine"
    if "schotter" in l:
        return "Schotter"
    if "splitt" in l or "split" in l:
        return "Splitt"
    if "fliesen" in l:
        return "Fliesen"
    if "silikon" in l:
        return "Silikon"
    if "gipskarton" in l or "rigips" in l:
        return "Gipskartonplatten"
    if "sanierputz" in l:
        return "Sanierputz"
    if "rohr" in l or "wasserleitung" in l:
        return "Rohrleitungen"
    if "fittings" in l:
        return "Fittings"
    if "pflanzsubstrat" in l or "erde" in l:
        return "Pflanzsubstrat"
    if "fliesenkleber" in l:
        return "Fliesenkleber"

    # Nur kurze, klare Materialbegriffe durchlassen.
    if re.search(r"\b\d+(?:[.,]\d+)?\b", l):
        return ""
    if len(t.split()) > 3:
        return ""
    return t


def build_human_summary(activities: list[str]) -> str:
    items = [str(a or "").strip() for a in activities if str(a or "").strip()]
    if not items:
        return "Keine Angabe"
    if len(items) == 1:
        return f"Auf der Baustelle {items[0]}."
    if len(items) == 2:
        return f"Auf der Baustelle {items[0]} sowie {items[1]}."
    return f"Auf der Baustelle {items[0]}, {items[1]} und {items[2]}."

