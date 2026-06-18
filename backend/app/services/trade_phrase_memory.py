from __future__ import annotations

import re

TRADE_PHRASE_MEMORY: dict[str, dict[str, object]] = {
    "galabau": {
        "keywords": ("pflaster", "schotter", "splitt", "pflanzkübel", "pflanzsubstrat", "randstein", "rasen", "unkraut", "hecke", "laub", "pflege", "palisade", "palisaden", "mulch", "rindenmulch", "keramik", "terrasse"),
        "preferred_verbs": ("eingebaut", "verlegt", "verdichtet", "gesetzt", "befüllt", "gemäht", "getrimmt", "entfernt", "geschnitten", "eingedeckt", "gemulcht"),
        "replacements": (
            (r"\bverarbeitung von schotter\b", "Schotter eingebaut"),
            (r"\bdurchführung von pflasterarbeiten\b", "Pflaster verlegt"),
            (r"\bbefüllung der pflanzkübel\b", "Pflanzkübel mit Erde befüllt"),
            (r"\bpflanzkübel mit erde befüllt\b", "Pflanzkübel mit Erde befüllt"),
            (r"\brasen gemacht\b", "Rasen gemäht"),
            (r"\brasse gemacht\b", "Rasen gemäht"),
            (r"\bunkraut zupfen\b", "Unkraut entfernt"),
            (r"\bunkraut weg gemacht\b", "Unkraut entfernt"),
            (r"\bschotter reingemacht\b", "Schotter eingebaut"),
            (r"\bmulch reingemacht\b", "Fläche mit Mulch eingedeckt"),
            (r"\brindenmulch reingemacht\b", "Rindenmulch eingedeckt"),
            (r"\bkeramik drauf gemacht\b", "Keramikterrasse verlegt"),
        ),
    },
    "trockenbau": {
        "keywords": ("trockenbau", "gipskarton", "rigips", "wand", "spachtel"),
        "preferred_verbs": ("montiert", "geschlossen", "verspachtelt"),
        "replacements": (
            (r"\bdurchführung von verspachtelungsarbeiten\b", "Spachtelarbeiten durchgeführt"),
            (r"\bmontagearbeiten durchgeführt\b", "Gipskartonplatten montiert"),
            (r"\bschließen einer trockenbauwand\b", "Trockenbauwand geschlossen"),
        ),
    },
    "shk": {
        "keywords": ("heizung", "wasserleitung", "rohr", "fittings", "anschluss", "sanitär", "wc", "toilette", "waschbecken", "dusche", "armatur"),
        "preferred_verbs": ("montiert", "angeschlossen", "verlegt", "eingebaut", "durchgeführt", "durchgefuehrt"),
        "replacements": (
            (r"\bheizungsanschlüsse hergestellt\b", "Heizungsanschlüsse montiert"),
            (r"\bwasserleitungen fertiggestellt\b", "Wasserleitungen verlegt"),
            (r"\bfittings hergestellt\b", "Fittings eingebaut"),
            (r"\bwc gesetzt\b|\btoilette eingebaut\b", "WC montiert"),
            (r"\bwaschbecken angebaut\b", "Waschbecken montiert"),
            (r"\bdusche angeschlossen\b", "Dusche montiert"),
            (r"\bdruckprobe gemacht\b", "Druckprüfung durchgeführt"),
            (r"\babgleich gemacht\b", "Hydraulischer Abgleich durchgeführt"),
        ),
    },
    "fliesenleger": {
        "keywords": ("fliesen", "fuge", "silikon", "fliese", "kleber", "nivelliermasse", "ausgleichsmasse", "bodenablauf", "naturstein"),
        "preferred_verbs": ("verlegt", "verfugt", "silikoniert"),
        "replacements": (
            (r"\bfliesenlegen durchgeführt\b", "Fliesen verlegt"),
            (r"\bsilikonfugen hergestellt\b", "Silikonfugen silikoniert"),
            (r"\bsilikonfugen gemacht\b", "Silikonfugen silikoniert"),
            (r"\bverfugungsarbeiten durchgeführt\b", "Fliesen verfugt"),
            (r"\bausgleichsmasse gezogen\b", "Nivelliermasse aufgetragen"),
            (r"\bbodenablauf gesetzt\b", "Bodenablauf eingebaut"),
            (r"\bgro(ß|ss)format verlegt\b", "Großformatfliesen verlegt"),
        ),
    },
    "sanierung": {
        "keywords": ("sanierputz", "altputz", "schimmel", "entfeuchtung", "sanierung", "sockelputz", "reibputz", "kratzputz"),
        "preferred_verbs": ("entfernt", "saniert", "aufgebracht", "aufgetragen"),
        "replacements": (
            (r"\bschimmelbeseitigung durchgeführt\b", "Schimmel beseitigt"),
            (r"\bentfernung des altputzes\b", "Altputz entfernt"),
            (r"\baufbringung von sanierputz\b", "Sanierputz aufgebracht"),
            (r"\bsockelputz gemacht\b", "Sockelputz aufgetragen"),
            (r"\breibputz gemacht\b", "Reibputz aufgetragen"),
            (r"\bkratzputz gemacht\b", "Kratzputz aufgetragen"),
        ),
    },
}


def _detect_trades(text: str) -> list[str]:
    probe = str(text or "").casefold()
    hits: list[str] = []
    for trade, cfg in TRADE_PHRASE_MEMORY.items():
        keywords = cfg.get("keywords") or ()
        for kw in keywords:
            k = str(kw).strip().casefold()
            if k and re.search(r"\b" + re.escape(k) + r"\b", probe):
                hits.append(trade)
                break
    return hits


def apply_trade_phrase_memory(activity: str, *, raw_text: str = "") -> str:
    out = str(activity or "").strip()
    if not out:
        return ""
    trades = _detect_trades(f"{raw_text} {out}")
    for trade in trades:
        cfg = TRADE_PHRASE_MEMORY.get(trade, {})
        replacements = cfg.get("replacements") or ()
        for pattern, repl in replacements:
            out = re.sub(str(pattern), str(repl), out, flags=re.IGNORECASE)
    out = re.sub(r"\s+", " ", out).strip(" ,.;")
    return out


def phrase_priority_boost(activity: str, *, raw_text: str = "") -> float:
    text = str(activity or "").casefold()
    trades = _detect_trades(f"{raw_text} {text}")
    boost = 0.0
    for trade in trades:
        cfg = TRADE_PHRASE_MEMORY.get(trade, {})
        verbs = cfg.get("preferred_verbs") or ()
        if any(str(v).casefold() in text for v in verbs):
            boost += 1.25
    return boost

