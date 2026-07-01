"""Welle 23: Kundengespräch-Vollständigkeit + Problem/Offen — ~25 Basisszenarien pro Gewerk.

Fokus: lange Run-on-Texte, Arbeiten → nach den Arbeiten → reiches Kundengespräch
(weiterempfehlen, gelobt, weitere Aufträge). Rein additiv.
"""

from __future__ import annotations

from typing import Any, Iterator

TRADES = ("GaLaBau", "Trockenbau", "Fliesen", "SHK", "Hochbau", "Tiefbau", "Putz")

_RICH_CUST = (
    "Nach den Arbeiten haben wir uns mit der Kundin unterhalten und die Kundin hat "
    "unsere Arbeit gelobt und freut sich auf weitere Auftraege und wird uns bei "
    "ihren Kollegen und Freunden weiterempfehlen."
)
_RICH_CUST2 = (
    "Anschließend mit der Kundin gesprochen sie hat die Qualitaet gelobt freut sich "
    "auf weitere Auftraege und wird uns weiterempfehlen."
)
_RICH_CUST3 = (
    "Danach Kundengespräch die Kundin war sehr zufrieden lobt unsere Arbeit und "
    "wird uns bei Nachbarn und Freunden weiterempfehlen."
)
_RICH_BAUHERR = (
    "Mit dem Bauherrn gesprochen er ist zufrieden freut sich auf die naechste Phase "
    "und wird uns weiterempfehlen."
)
_RICH_AUFTRAGGEBER = (
    "Mit dem Auftraggeber unterhalten er lobt unsere Arbeit freut sich auf weitere "
    "Auftraege und empfiehlt uns weiter."
)

_VOCAB: dict[str, dict[str, Any]] = {
    "GaLaBau": {
        "w1": "50 Quadratmeter Pflaster gelegt",
        "w2": "5 Quadratmeter Gartenmauer gebaut",
        "w3": "15 Meter Hecke geschnitten",
        "w4": "40 Quadratmeter Rasen verlegt",
        "w5": "20 laufende Meter Palisaden gesetzt",
        "acts": (
            ("50 m² Pflaster verlegt", "Gartenmauer gebaut", "Hecke geschnitten"),
            ("40 m² Rasen verlegt", "Hecke geschnitten"),
            ("Palisaden gesetzt", "30 m² Pflaster verlegt"),
            ("Hecke geschnitten",),
            ("60 m² Pflaster verlegt", "Schotter eingebaut"),
        ),
        "mats": ("Pflastersteine", "Schotter"),
        "cust_not": ("50", "5", "15", "40", "quadratmeter", "pflaster", "gartenmauer", "hecke", "rasen", "palisaden"),
        "prob": "Problem Lieferung Pflastersteine zu spaet",
        "open": "Offen letzte Reihe morgen",
        "prob_must": ("liefer", "spät"),
        "open_must": ("reihe", "morgen", "offen"),
    },
    "Trockenbau": {
        "w1": "Zwei Trennwände geschlossen",
        "w2": "45 Quadratmeter Gipskarton montiert",
        "w3": "Decke abgehängt",
        "w4": "Ständerwerk montiert",
        "w5": "Fugen gespachtelt und geschliffen",
        "acts": (
            ("Trockenbauwand geschlossen", "Gipskartonplatten montiert"),
            ("Gipskartonplatten montiert",),
            ("Decke abgehängt",),
            ("Ständerwerk montiert",),
            ("Fugen gespachtelt",),
        ),
        "mats": ("Gipskartonplatten",),
        "cust_not": ("gipskarton", "trennwand", "decke", "45", "quadratmeter", "ständerwerk", "geschlossen"),
        "prob": "Problem Akustikdaemmung knapp",
        "open": "Offen Restspachtel morgen",
        "prob_must": ("akustik", "knapp"),
        "open_must": ("spachtel", "morgen", "offen"),
    },
    "Fliesen": {
        "w1": "18 Quadratmeter Fliesen im Bad verlegt",
        "w2": "32 Quadratmeter Grossformatfliesen verlegt",
        "w3": "Silikonfugen im WC gemacht",
        "w4": "Bodenfliesen 25 qm verlegt",
        "w5": "Wandfliesen im Duschbereich gesetzt",
        "acts": (
            ("18 m² Fliesen verlegt",),
            ("32 m² Fliesen verlegt",),
            ("Silikonfugen",),
            ("25 m² Fliesen verlegt",),
            ("Wandfliesen gesetzt",),
        ),
        "mats": ("Fliesen", "Fliesenkleber"),
        "cust_not": ("18", "32", "25", "fliesen verlegt", "quadratmeter", "bad", "wc"),
        "prob": "Problem Wand nicht lotrecht",
        "open": "Offen Silikonfugen morgen",
        "prob_must": ("lotrecht",),
        "open_must": ("silikon", "morgen", "offen"),
    },
    "SHK": {
        "w1": "Heizkoerper getauscht",
        "w2": "Thermostatventile eingebaut",
        "w3": "WC montiert und Spuelkasten angeschlossen",
        "w4": "Rohrleitung verlegt",
        "w5": "Fußbodenheizung verlegt",
        "acts": (
            ("Heizkörper getauscht", "Thermostatventile eingebaut"),
            ("Thermostatventile eingebaut",),
            ("WC montiert",),
            ("Rohrleitung verlegt",),
            ("Fußbodenheizung verlegt",),
        ),
        "mats": ("Thermostatventile",),
        "cust_not": ("heizkörper", "thermostat", "wc", "rohr", "fußboden", "getauscht", "montiert"),
        "prob": "Problem Dichtung undicht",
        "open": "Offen Entlueftung morgen",
        "prob_must": ("dichtung", "undicht"),
        "open_must": ("entlueft", "morgen", "offen"),
    },
    "Hochbau": {
        "w1": "Fundament betoniert",
        "w2": "Mauerwerk hochgezogen",
        "w3": "Bewehrung eingebaut",
        "w4": "Decke geschalt",
        "w5": "Fassadengeruest aufgestellt",
        "acts": (
            ("Fundament betoniert", "Bewehrung eingebaut"),
            ("Mauerwerk hochgezogen",),
            ("Bewehrung eingebaut",),
            ("Decke geschalt",),
            ("Fassadengerüst aufgestellt",),
        ),
        "mats": ("Beton",),
        "cust_not": ("fundament", "mauerwerk", "bewehrung", "decke", "gerüst", "betoniert"),
        "prob": "Problem Betonpumpe verspaetet",
        "open": "Offen Abziehen morgen",
        "prob_must": ("betonpumpe", "verspätet"),
        "open_must": ("abziehen", "morgen", "offen"),
    },
    "Tiefbau": {
        "w1": "Kanalgraben 12 Meter ausgehoben",
        "w2": "KG-Rohr DN 300 verlegt",
        "w3": "Schottertragschicht eingebaut",
        "w4": "Betonfundament gegossen",
        "w5": "Asphaltdecke 80 Quadratmeter eingebaut",
        "acts": (
            ("Kanalgraben ausgehoben", "KG-Rohr verlegt"),
            ("KG-Rohr verlegt",),
            ("Schotter eingebaut",),
            ("Fundament betoniert",),
            ("Asphalt eingebaut",),
        ),
        "mats": ("KG-Rohr", "Schotter"),
        "cust_not": ("kanal", "rohr", "schotter", "asphalt", "12", "80", "meter", "quadratmeter"),
        "prob": "Problem Grundwasser steht",
        "open": "Offen Verfuellung morgen",
        "prob_must": ("grundwasser", "wasser"),
        "open_must": ("verfuell", "morgen", "offen"),
    },
    "Putz": {
        "w1": "Aussenputz 120 Quadratmeter aufgetragen",
        "w2": "Innenputz 45 Quadratmeter gespachtelt",
        "w3": "Sockelputz gesetzt",
        "w4": "Fassade grundiert",
        "w5": "Putzprofil montiert",
        "acts": (
            ("Außenputz aufgetragen",),
            ("Innenputz gespachtelt",),
            ("Sockelputz gesetzt",),
            ("Fassade grundiert",),
            ("Putzprofil montiert",),
        ),
        "mats": ("Putzmörtel",),
        "cust_not": ("putz", "120", "45", "quadratmeter", "fassade", "sockel"),
        "prob": "Problem Trocknung zu langsam",
        "open": "Offen zweiter Anstrich Freitag",
        "prob_must": ("trocknung", "langsam"),
        "open_must": ("anstrich", "freitag", "offen"),
    },
}


def _rich_fields(vocab: dict, extra_must: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "customer": True,
        "cust_rich": True,
        "cust_must": ("weiterempfehl", "gelobt") + extra_must,
        "cust_not": tuple(vocab["cust_not"]),
    }


def _build_trade_scenarios(trade: str) -> list[dict[str, Any]]:
    v = _VOCAB[trade]
    cn = tuple(v["cust_not"])
    acts = v["acts"]
    scenarios: list[dict[str, Any]] = []

    # 1 — Nutzer-Anker: drei Arbeiten + reiches Kundengespräch
    scenarios.append({
        "raw": (
            f"Heute haben wir {v['w1']} {v['w2']} und danach haben wir {v['w3']} "
            f"{_RICH_CUST}"
        ),
        "acts": acts[0],
        "mats": tuple(v.get("mats") or ()),
        "mat_echo": bool(v.get("mats")),
        **_rich_fields(v),
    })

    # 2 — Zwei Arbeiten + reiches Kundengespräch Variante 2
    scenarios.append({
        "raw": f"{v['w1']} und {v['w4']} {_RICH_CUST2}",
        "acts": acts[1],
        **_rich_fields(v),
    })

    # 3 — Eine Arbeit + reiches Kundengespräch Variante 3
    scenarios.append({
        "raw": f"{v['w2']} {_RICH_CUST3}",
        "acts": acts[1][:1] if len(acts[1]) > 1 else acts[1],
        **_rich_fields(v, ("zufrieden",)),
    })

    # 4 — Arbeiten + Problem + Offen + Kundin zufrieden
    scenarios.append({
        "raw": (
            f"{v['w1']} {v['w3']} {v['prob']} {v['open']} "
            "mit der Kundin gesprochen sie ist zufrieden."
        ),
        "acts": acts[0][:2] if len(acts[0]) > 2 else acts[0],
        "problem": True,
        "open_": True,
        "customer": True,
        "cust_must": ("gesprochen", "zufrieden"),
        "cust_not": cn,
        "prob_must": tuple(v["prob_must"]),
        "prob_not": cn[:4],
        "open_must": tuple(v["open_must"]),
        "open_not": cn[:3],
    })

    # 5 — Arbeit + Problem + Offen + Bauherr informiert
    scenarios.append({
        "raw": f"{v['w1']}. {v['prob']}. {v['open']}. Bauherr kurz informiert.",
        "acts": acts[0][:1],
        "problem": True,
        "open_": True,
        "customer": True,
        "cust_must": ("informiert", "bauherr"),
        "cust_not": cn,
        "prob_must": tuple(v["prob_must"]),
        "open_must": tuple(v["open_must"]),
    })

    # 6 — Nur Arbeiten (Summary-Check)
    scenarios.append({
        "raw": f"{v['w1']} {v['w2']} {v['w5']}",
        "acts": acts[0],
        "min_act": 1,
    })

    # 7 — Nur reiches Kundengespräch
    scenarios.append({
        "raw": _RICH_CUST,
        "acts": (),
        "min_act": 0,
        **_rich_fields(v),
    })

    # 8 — Problem + Offen ohne Kunde
    scenarios.append({
        "raw": f"{v['w3']} {v['prob']} {v['open']}",
        "acts": acts[3],
        "problem": True,
        "open_": True,
        "prob_must": tuple(v["prob_must"]),
        "open_must": tuple(v["open_must"]),
    })

    # 9 — Arbeit + Problem + Kunde
    scenarios.append({
        "raw": (
            f"{v['w1']} {v['prob']} mit dem Kunden gesprochen er ist einverstanden."
        ),
        "acts": acts[0][:1],
        "problem": True,
        "customer": True,
        "cust_must": ("gesprochen", "einverstanden"),
        "cust_not": cn,
        "prob_must": tuple(v["prob_must"]),
        "prob_not": cn[:3],
    })

    # 10 — Arbeit + Offen + reiches Kundengespräch
    scenarios.append({
        "raw": f"{v['w2']} {v['open']} {_RICH_CUST2}",
        "acts": acts[1][:1] if acts[1] else acts[2],
        "open_": True,
        "open_must": tuple(v["open_must"]),
        **_rich_fields(v),
    })

    # 11 — Kundengespräch gehabt + Muster/Farbe
    scenarios.append({
        "raw": (
            f"Kundengespräch gehabt Farbton abgestimmt {v['prob']} {v['open']}"
        ),
        "acts": (),
        "min_act": 0,
        "problem": True,
        "open_": True,
        "customer": True,
        "cust_must": ("kundengespräch", "abgestimmt"),
        "prob_must": tuple(v["prob_must"]),
        "open_must": tuple(v["open_must"]),
    })

    # 12 — Auftraggeber reich
    scenarios.append({
        "raw": f"{v['w1']} {_RICH_AUFTRAGGEBER}",
        "acts": acts[0][:1],
        **_rich_fields(v, ("auftraggeber",)),
    })

    # 13 — Bauherr reich
    scenarios.append({
        "raw": f"{v['w3']} {_RICH_BAUHERR}",
        "acts": acts[2],
        **_rich_fields(v, ("bauherr",)),
    })

    # 14 — Run-on ohne Punkte
    scenarios.append({
        "raw": (
            f"heute {v['w1']} und {v['w2']} und {v['w3']} nach den arbeiten "
            "kundin gelobt freut sich auf weitere auftraege weiterempfehlen kollegen freunden"
        ),
        "acts": acts[0],
        **_rich_fields(v),
    })

    # 15 — Vier Arbeiten + Kunde
    scenarios.append({
        "raw": (
            f"{v['w1']} {v['w2']} {v['w3']} {v['w4']} "
            "Nach den Arbeiten mit der Kundin unterhalten sie lobt uns und empfiehlt uns weiter."
        ),
        "acts": acts[0],
        "customer": True,
        "cust_rich": True,
        "cust_must": ("unterhalten", "lobt", "weiterempfehl"),
        "cust_not": cn,
    })

    # 16 — Arbeit + Problem only
    scenarios.append({
        "raw": f"{v['w4']} {v['prob']}",
        "acts": acts[3],
        "problem": True,
        "prob_must": tuple(v["prob_must"]),
    })

    # 17 — Arbeit + Offen only
    scenarios.append({
        "raw": f"{v['w5']} {v['open']}",
        "acts": acts[4],
        "open_": True,
        "open_must": tuple(v["open_must"]),
    })

    # 18 — Material-Echo Guard
    scenarios.append({
        "raw": f"{v['w2']} Material zum Einsatz gekommen.",
        "acts": acts[1][:1] if acts[1] else acts[2],
        "mats": tuple(v.get("mats") or ()),
        "mat_echo": True,
        "sum_forbid": ("zum einsatz", "dafür kamen"),
    })

    # 19 — Happy Kundin
    scenarios.append({
        "raw": (
            f"{v['w1']} Nach den Arbeiten Kundin happy mit der Arbeit "
            "freut sich auf weitere Auftraege."
        ),
        "acts": acts[0][:1],
        "customer": True,
        "cust_rich": True,
        "cust_must": ("happy", "auftrag"),
        "cust_not": cn,
    })

    # 20 — Rücksprache abgestimmt
    scenarios.append({
        "raw": "Mit dem Kunden Rücksprache gehalten nächster Termin abgestimmt.",
        "acts": (),
        "min_act": 0,
        "customer": True,
        "cust_must": ("rücksprache", "abgestimmt"),
        "cust_not": ("verlegt", "m²", "quadratmeter"),
    })

    # 21 — Problem + Offen + Bauleitung
    scenarios.append({
        "raw": (
            f"{v['w1']} {v['w2']} {v['prob']} {v['open']} Bauleitung informiert."
        ),
        "acts": acts[0][:2] if len(acts[0]) > 1 else acts[0],
        "problem": True,
        "open_": True,
        "customer": True,
        "cust_must": ("informiert", "bauleitung"),
        "cust_not": cn,
        "prob_must": tuple(v["prob_must"]),
        "open_must": tuple(v["open_must"]),
    })

    # 22 — Anschließend unterhalten einverstanden weiterempfehlen
    scenarios.append({
        "raw": (
            f"{v['w1']} {v['w3']} Anschließend mit der Kundin unterhalten "
            "sie ist einverstanden lobt die Arbeit und wird uns weiterempfehlen."
        ),
        "acts": acts[0][:2] if len(acts[0]) > 1 else acts[0],
        **_rich_fields(v, ("einverstanden",)),
    })

    # 23 — Problem + Offen + Kundin (Kundenteil klar abgetrennt)
    scenarios.append({
        "raw": (
            f"{v['w5']}. {v['prob']}. {v['open']}. "
            "Kundin vor Ort zufrieden mit dem Fortschritt."
        ),
        "acts": acts[4],
        "problem": True,
        "open_": True,
        "customer": True,
        "cust_must": ("zufrieden", "kundin"),
        "cust_not": cn,
        "prob_must": tuple(v["prob_must"]),
        "open_must": tuple(v["open_must"]),
    })

    # 24 — Mega-Kette punctuiert
    scenarios.append({
        "raw": (
            f"Heute {v['w1']}. Dann {v['w2']}. Danach {v['w3']}. "
            f"{_RICH_CUST}"
        ),
        "acts": acts[0],
        **_rich_fields(v),
    })

    # 25 — Work forbid + customer isolation streng
    scenarios.append({
        "raw": (
            f"{v['w1']} {v['w2']} verarbeitet {v['prob']} {v['open']} "
            f"{_RICH_CUST3}"
        ),
        "acts": acts[0][:2] if len(acts[0]) > 1 else acts[0],
        "forbid_acts": (f"{trade} verarbeitet",),
        "problem": True,
        "open_": True,
        **_rich_fields(v),
        "prob_must": tuple(v["prob_must"]),
        "open_must": tuple(v["open_must"]),
    })

    return scenarios[:25]


TRADE_SCENARIOS: dict[str, list[dict[str, Any]]] = {
    trade: _build_trade_scenarios(trade) for trade in TRADES
}


def all_base_scenarios() -> Iterator[tuple[str, dict[str, Any]]]:
    for trade in TRADES:
        for spec in TRADE_SCENARIOS[trade]:
            yield trade, spec
