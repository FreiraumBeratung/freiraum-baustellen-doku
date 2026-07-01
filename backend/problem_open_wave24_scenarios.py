"""Welle 24: P3 Live-Tuning — implizite Probleme/Offen, alle 7 Gewerke.

~15 Basisszenarien pro Gewerk: Regen/Abbrechen, morgen müssen wir, Untergrund,
dementsprechend weitermachen, explizite Marker. Rein additiv.
"""

from __future__ import annotations

from typing import Any, Iterator

TRADES = ("GaLaBau", "Trockenbau", "Fliesen", "SHK", "Hochbau", "Tiefbau", "Putz")

_VOCAB: dict[str, dict[str, Any]] = {
    "GaLaBau": {
        "work": "heute haben wir 50 Quadratmeter Pflaster gelegt und 5 Quadratmeter Gartenmauer gebaut",
        "work2": "heute haben wir 50 Quadratmeter Pflaster gelegt",
        "rain": "leider mussten wir die Arbeiten abbrechen weil es geregnet hat",
        "rain2": "wir mussten die Arbeiten leider abbrechen weil es angefangen hat zu regnen",
        "uneben": "leider war der Untergrund sehr uneben was zu Problemen geführt hat",
        "open": "morgen müssen wir noch fünf weitere Quadratmeter legen",
        "open2": "morgen müssen wir noch 20 Meter Hecke schneiden",
        "plan": "dementsprechend werden wir morgen dort weitermachen",
        "cust": "die Kundin war trotzdem zufrieden mit unserer Arbeit und freut sich auf weitere Auftraege",
        "prob_exp": "Problem Lieferung Pflastersteine zu spaet",
        "open_exp": "Offen letzte Reihe morgen",
        "prob_must": ("regen", "unterbrochen"),
        "prob_must2": ("uneben",),
        "prob_must_rain2": ("regen", "unterbrochen"),
        "open_must": ("morgen", "offen"),
        "prob_trade": ("liefer", "spät"),
        "open_trade": ("reihe", "morgen"),
    },
    "Trockenbau": {
        "work": "heute haben wir zwei Trennwände geschlossen und 45 Quadratmeter Gipskarton montiert",
        "work2": "heute haben wir Decke abgehängt",
        "rain": "leider mussten wir wegen Staub im Treppenhaus die Arbeiten abbrechen",
        "rain2": "mussten die Arbeiten abbrechen weil die Lieferung zu spaet kam",
        "uneben": "leider war die Wand sehr uneben was zu Problemen geführt hat",
        "open": "morgen müssen wir noch die Spachtelarbeiten fertigstellen",
        "open2": "morgen müssen wir noch Rigips Rest montieren",
        "plan": "dementsprechend machen wir morgen den Rest",
        "cust": "der Bauherr war kurz da und ist zufrieden",
        "prob_exp": "Problem Akustikdaemmung knapp",
        "open_exp": "Offen Spachtel morgen",
        "prob_must": ("abbrechen",),
        "prob_must2": ("uneben",),
        "prob_must_rain2": ("liefer", "spaet", "unterbrochen"),
        "open_must": ("morgen", "offen"),
        "prob_trade": ("akustik", "knapp"),
        "open_trade": ("spachtel", "morgen"),
    },
    "Fliesen": {
        "work": "heute haben wir 18 Quadratmeter Fliesen im Bad verlegt",
        "work2": "heute haben wir 32 Quadratmeter Grossformatfliesen verlegt",
        "rain": "mussten leider abbrechen weil der Kleber zu schnell abbindet bei Hitze",
        "rain2": "wir mussten die Arbeiten abbrechen weil die Wand nicht lotrecht ist",
        "uneben": "leider war die Wand sehr uneben was zu Problemen geführt hat",
        "open": "morgen müssen wir noch die Silikonfugen ziehen",
        "open2": "morgen müssen wir noch Restfliesen verlegen",
        "plan": "dementsprechend werden wir morgen die Fugen fertig machen",
        "cust": "die Kundin hat die Farbe bestätigt und ist zufrieden",
        "prob_exp": "Problem Wand nicht lotrecht",
        "open_exp": "Offen Silikon morgen",
        "prob_must": ("kleber", "hitze", "unterbrochen"),
        "prob_must2": ("uneben",),
        "prob_must_rain2": ("lotrecht", "unterbrochen"),
        "open_must": ("morgen", "offen"),
        "prob_trade": ("lotrecht",),
        "open_trade": ("silikon", "morgen"),
    },
    "SHK": {
        "work": "heute haben wir Heizkoerper getauscht und Thermostatventile eingebaut",
        "work2": "heute haben wir WC montiert",
        "rain": "mussten abbrechen weil die Dichtung undicht war",
        "rain2": "leider mussten wir stoppen weil Pressfitting fehlt",
        "uneben": "Problem Anschluss zu eng was zu Problemen geführt hat",
        "open": "morgen müssen wir noch die Entlueftung machen",
        "open2": "morgen müssen wir noch die Rohrleitung fertig verlegen",
        "plan": "dementsprechend werden wir morgen weitermachen",
        "cust": "mit dem Kunden gesprochen er ist zufrieden",
        "prob_exp": "Problem Dichtung undicht",
        "open_exp": "Offen Entlueftung morgen",
        "prob_must": ("dichtung", "undicht", "unterbrochen"),
        "prob_must2": ("eng", "anschluss"),
        "prob_must_stop": ("pressfitting", "fehlt"),
        "prob_must_rain2": ("pressfitting", "fehlt"),
        "open_must": ("morgen", "offen"),
        "prob_trade": ("dichtung",),
        "open_trade": ("entlueft", "morgen"),
    },
    "Hochbau": {
        "work": "heute haben wir Fundament betoniert und Bewehrung eingebaut",
        "work2": "heute haben wir Mauerwerk hochgezogen",
        "rain": "mussten abbrechen weil die Betonpumpe verspaetet kam",
        "rain2": "leider mussten wir wegen Regen die Arbeiten abbrechen",
        "uneben": "leider war das Gefaelle falsch was zu Problemen geführt hat",
        "open": "morgen müssen wir noch das Fundament abziehen",
        "open2": "morgen müssen wir noch die Decke schalen",
        "plan": "dementsprechend betonieren wir morgen weiter",
        "cust": "Bauherr kurz informiert",
        "prob_exp": "Problem Betonpumpe verspaetet",
        "open_exp": "Offen Abziehen morgen",
        "prob_must": ("abbrechen", "unterbrochen"),
        "prob_must2": ("gefälle", "gefaelle"),
        "prob_must_rain2": ("regen", "unterbrochen"),
        "open_must": ("morgen", "offen"),
        "prob_trade": ("betonpumpe",),
        "open_trade": ("abziehen", "morgen"),
    },
    "Tiefbau": {
        "work": "heute haben wir Kanalgraben ausgehoben und KG-Rohr verlegt",
        "work2": "heute haben wir Schotter eingebaut",
        "rain": "mussten abbrechen weil Grundwasser im Graben stand",
        "rain2": "leider mussten wir wegen Regen stoppen",
        "uneben": "Problem Gefaelle zu flach was zu Problemen geführt hat",
        "open": "morgen müssen wir noch die Verfuellung machen",
        "open2": "morgen müssen wir noch Asphalt einbauen",
        "plan": "dementsprechend werden wir morgen den Graben verfuellen",
        "cust": "Bauleitung informiert",
        "prob_exp": "Problem Wasser im Graben",
        "open_exp": "Offen Verfuellung morgen",
        "prob_must": ("grundwasser", "wasser", "unterbrochen"),
        "prob_must2": ("gefälle", "gefaelle"),
        "prob_must_rain2": ("regen", "unterbrochen"),
        "open_must": ("morgen", "offen"),
        "prob_trade": ("wasser", "graben"),
        "open_trade": ("verfuell", "morgen"),
    },
    "Putz": {
        "work": "heute haben wir grundiert und den Unterputz aufgetragen",
        "work2": "heute haben wir 120 Quadratmeter Aussenputz aufgetragen",
        "rain": "mussten abbrechen weil der Putz bei Regen nicht trocknet",
        "rain2": "leider mussten wir wegen Wind die Arbeiten abbrechen",
        "uneben": "leider war der Untergrund sehr uneben was zu Problemen geführt hat",
        "open": "morgen müssen wir auf der Baustelle mit Oberputz abschliessen",
        "open2": "morgen müssen wir noch den zweiten Anstrich auftragen",
        "plan": "dementsprechend schliessen wir morgen mit Oberputz ab",
        "cust": "die Kundin ist zufrieden mit dem Fortschritt",
        "prob_exp": "Problem Trocknung zu langsam",
        "open_exp": "Offen Anstrich Freitag",
        "prob_must": ("abbrechen", "unterbrochen"),
        "prob_must2": ("uneben",),
        "prob_must_rain2": ("wind", "unterbrochen"),
        "open_must": ("morgen", "offen"),
        "prob_trade": ("trocknung", "langsam"),
        "open_trade": ("anstrich", "freitag"),
    },
}


def _build_trade_scenarios(trade: str) -> list[dict[str, Any]]:
    v = _VOCAB[trade]
    s: list[dict[str, Any]] = []

    # 1 — Live: Regen + morgen offen
    s.append({
        "raw": f"{v['work']} {v['rain']} {v['open']}",
        "problem": True, "open_": True,
        "prob_must": v["prob_must"], "open_must": v["open_must"],
        "prob_not": ("50", "pflaster", "gartenmauer", "quadratmeter"),
        "open_not": ("50", "pflaster", "abbrechen"),
    })
    # 2 — Regen nur
    s.append({
        "raw": f"{v['work2']} {v['rain2']}",
        "problem": True,
        "prob_must": v.get("prob_must_stop", v.get("prob_must_rain2", v["prob_must"])),
    })
    # 3 — Untergrund + Kunde
    s.append({
        "raw": f"{v['work2']} {v['uneben']} {v['cust']}",
        "problem": True, "customer": True,
        "prob_must": v["prob_must2"],
        "prob_not": ("kundin", "zufrieden", "auftrag"),
        "cust_must": ("zufrieden",),
        "cust_not": ("quadratmeter", "verlegt", "montiert", "uneben"),
    })
    # 4 — morgen Arbeit offen
    s.append({
        "raw": f"{v['work2']} {v['open2']}",
        "open_": True,
        "open_must": v["open_must"],
        "open_not": ("verlegt", "montiert"),
    })
    # 5 — Putz/Oberputz Stil
    s.append({
        "raw": f"{v['work']} {v['open']}",
        "open_": True,
        "open_must": v["open_must"] + ("oberputz", "abschlie") if trade == "Putz" else v["open_must"],
    })
    # 6 — explizit Problem + Offen
    s.append({
        "raw": f"{v['work2']} {v['prob_exp']} {v['open_exp']}",
        "problem": True, "open_": True,
        "prob_must": v["prob_trade"], "open_must": v["open_trade"],
    })
    # 7 — dementsprechend morgen (nur offen)
    s.append({
        "raw": f"{v['work2']} {v['rain2']} {v['plan']}",
        "problem": True, "open_": True,
        "prob_must": v.get("prob_must_rain2", ("unterbrochen", "regen")),
        "open_must": ("morgen", "offen"),
        "prob_not": ("weitermachen", "dementsprechend"),
    })
    # 8 — nur explizites Problem
    s.append({
        "raw": f"{v['work2']} {v['prob_exp']}",
        "problem": True,
        "prob_must": v["prob_trade"],
    })
    # 9 — nur explizites Offen
    s.append({
        "raw": f"{v['work2']} {v['open_exp']}",
        "open_": True,
        "open_must": v["open_trade"],
    })
    # 10 — Run-on alles
    s.append({
        "raw": f"{v['work']} {v['rain']} {v['open']} {v['cust']}",
        "problem": True, "open_": True, "customer": True,
        "prob_must": v["prob_must"], "open_must": v["open_must"],
        "cust_not": ("abbrechen", "morgen", "regen"),
    })
    # 11 — nur Arbeit
    s.append({"raw": v["work"], "min_act": 1})
    # 12 — Problem + Kunde ohne offen
    s.append({
        "raw": f"{v['work2']} {v['prob_exp']} {v['cust']}",
        "problem": True, "customer": True,
        "prob_must": v["prob_trade"],
        "cust_must": ("zufrieden",),
    })
    # 13 — leider abbrechen kurz
    s.append({
        "raw": f"{v['work2']} leider mussten wir abbrechen wegen schlechtem Wetter",
        "problem": True,
        "prob_must": ("unterbrochen", "wetter"),
    })
    # 14 — morgen ohne müssen
    s.append({
        "raw": f"{v['work2']} morgen noch Rest fertig machen",
        "open_": True,
        "open_must": ("morgen", "offen"),
    })
    # 15 — großes Problem explizit + offen getrennt
    s.append({
        "raw": f"{v['work2']} das war ein sehr grosses Problem wegen der Lieferung. {v['open']}",
        "problem": True, "open_": True,
        "prob_must": ("liefer", "problem"),
        "open_must": v["open_must"],
    })

    return s[:15]


TRADE_SCENARIOS: dict[str, list[dict[str, Any]]] = {
    trade: _build_trade_scenarios(trade) for trade in TRADES
}


def all_base_scenarios() -> Iterator[tuple[str, dict[str, Any]]]:
    for trade in TRADES:
        for spec in TRADE_SCENARIOS[trade]:
            yield trade, spec
