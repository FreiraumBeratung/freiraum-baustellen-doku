"""Generator Pilot-Welle 29 — 100 Szenarien × GaLaBau, Tiefbau, Straßenbau (300 gesamt).

Einmal ausführen: python _gen_pilot_gala_tief_strasse_wave29_scenarios.py
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).parent / "pilot_gala_tief_strasse_wave29_scenarios.py"
TRADES = ("GaLaBau", "Tiefbau", "Strassenbau")
TARGET_PER_TRADE = 100


def s(raw: str, acts: tuple[str, ...], **kw) -> dict:
    d = dict(
        raw=raw,
        acts=acts,
        mats=(),
        forbid_acts=(),
        problem=False,
        open_=False,
        customer=False,
        min_act=None,
    )
    d.update(kw)
    return d


VOCAB: dict[str, dict] = {
    "GaLaBau": dict(
        w1="50 Quadratmeter Pflaster verlegt und 5 laufende Meter Rasenkantensteine gesetzt",
        w2="40 Quadratmeter Terrassenplatten verlegt zwei Kubikmeter Schotter eingebaut",
        w3="Hecke zurückgeschnitten Rindenmulch eingedeckt",
        w4="30 Quadratmeter Rollrasen verlegt Palisaden gesetzt",
        w5="Unkraut entfernt Laub gefegt",
        rain="leider mussten wir die Arbeiten abbrechen weil es geregnet hat",
        rain2="wir mussten die Arbeiten abbrechen weil es angefangen hat zu regnen",
        uneben="leider war der Untergrund sehr uneben was zu Problemen geführt hat",
        open="morgen müssen wir noch fünf weitere Quadratmeter legen",
        open2="morgen müssen wir noch 20 Meter Hecke schneiden",
        plan="dementsprechend werden wir morgen dort weitermachen",
        cust="die Kundin war zufrieden mit unserer Arbeit",
        cust2="mit dem Bauherr kurz gesprochen er ist einverstanden",
        prob="Problem Lieferung Pflastersteine zu spät",
        open_exp="Offen letzte Reihe morgen",
        a1=("Pflaster verlegt", "Rasenkantensteine"),
        a2=("Terrassenplatten", "Schotter"),
        a3=("Hecke geschnitten", "Rindenmulch"),
        a4=("Rasen verlegt", "Palisaden"),
        a5=("Unkraut entfernt", "Laub"),
        mats=(),
    ),
    "Tiefbau": dict(
        w1="25 laufende Meter Kanalgraben ausgehoben KG-Rohre DN 110 verlegt Graben verfüllt",
        w2="drei Kubikmeter Schotter eingebaut und verdichtet Planum hergestellt",
        w3="Frostschutz eingebaut Schottertragschicht hergestellt",
        w4="Leitungstrasse hergestellt Hausanschluss hergestellt",
        w5="Drainage verlegt Geotextil eingebaut",
        rain="mussten abbrechen weil Grundwasser im Graben stand",
        rain2="leider mussten wir wegen Regen stoppen",
        uneben="Problem Gefälle zu flach was zu Problemen geführt hat",
        open="morgen müssen wir noch die Verfüllung machen",
        open2="morgen müssen wir noch Asphalt einbauen",
        plan="dementsprechend werden wir morgen den Graben verfüllen",
        cust="Bauleitung informiert",
        cust2="Mit der Bauleitung abgestimmt",
        prob="Problem Wasser im Graben",
        open_exp="Offen Verfüllung morgen",
        a1=("Graben ausgehoben", "KG-Rohre", "Graben verfüllt"),
        a2=("Schotter eingebaut", "Planum"),
        a3=("Frostschutz", "Schottertragschicht"),
        a4=("Leitungstrasse", "Hausanschluss"),
        a5=("Drainage", "Geotextil"),
        mats=(),
    ),
    "Strassenbau": dict(
        w1="15 laufende Meter Asphalt geschnitten 30 Quadratmeter asphaltiert 30 Quadratmeter Pflaster verlegt 15 laufende Meter Rasenkantensteine gesetzt",
        w2="Kopfloch ausgehoben 11 Meter Asphalt schneiden 24 Quadratmeter asphaltiert",
        w3="Frostschutz eingebaut Schotter eingebaut Planum verdichtet Asphalt eingebaut",
        w4="Hochbord gesetzt Rinnensteine verlegt Gully gesetzt",
        w5="Deckschicht abgefräst 18 Quadratmeter SMA asphaltiert",
        rain="Problem Temperatur zu niedrig mussten abbrechen",
        rain2="leider Maschine kaputt mussten stoppen",
        uneben="Problem Untergrund uneben",
        open="Offen letzte Bahn morgen",
        open2="morgen müssen wir noch Asphalt einbauen",
        plan="dementsprechend asphaltieren wir morgen weiter",
        cust="Bauherr kurz da Kundengespräch lief gut",
        cust2="Auftraggeber informiert",
        prob="Problem Verkehrssicherung",
        open_exp="Offen Abschluss Freitag",
        a1=("Asphalt schneiden", "Asphalt eingebaut", "Pflaster verlegt", "Rasenkantensteine"),
        a2=("Graben ausgehoben", "Asphalt schneiden", "Asphalt eingebaut"),
        a3=("Frostschutz", "Schotter", "Asphalt eingebaut"),
        a4=("Borde gesetzt", "Rinnensteine", "Straßenabläufe"),
        a5=("Asphalt fräsen", "Asphalt eingebaut"),
        mats=(),
    ),
}


def _core_live(v: dict, trade: str) -> list[dict]:
    return [
        s(f"Morgens {v['w1']} {v['rain']} {v['open']} {v['cust']}.", v["a1"], problem=True, open_=True, customer=True, min_act=2),
        s(f"{v['w2']} {v['rain2']}.", v["a2"], problem=True, min_act=1),
        s(f"{v['w3']} {v['uneben']} {v['cust2']}.", v["a3"], problem=True, customer=True, min_act=1),
        s(f"{v['w4']} {v['open2']}.", v["a4"], open_=True, min_act=1),
        s(f"{v['w5']} {v['prob']} {v['open_exp']}.", v["a5"], problem=True, open_=True, min_act=1),
        s(f"{v['w1']} {v['plan']}.", v["a1"], open_=True, min_act=2),
        s(f"{v['w2']} {v['cust']}.", v["a2"], customer=True, min_act=1),
        s(f"Heute nur {v['cust2']} wegen Termin keine Arbeit wegen Regen.", (), problem=True, customer=True, min_act=0),
    ]


def _explicit_p23(v: dict) -> list[dict]:
    return [
        s(f"{v['w3']} Problem Material knapp Offen Rest morgen.", v["a3"], problem=True, open_=True, min_act=1),
        s(f"{v['w2']} Problem Lieferung fehlt Offen nächste Woche.", v["a2"], problem=True, open_=True, min_act=1),
        s(f"{v['w1']} leider mussten wir abbrechen morgen weiter.", v["a1"], problem=True, open_=True, min_act=1),
        s(f"{v['w5']} Kundengespräch mit Bauleitung Abstimmung Termin.", v["a5"], customer=True, min_act=1),
        s("Problem Werkzeug defekt Offen Ersatz morgen.", (), problem=True, open_=True, min_act=0),
        s(f"{v['w4']} Bauherr zufrieden.", v["a4"], customer=True, min_act=1),
    ]


def _chains(v: dict, trade: str) -> list[dict]:
    items = [
        s(v["w1"], v["a1"], min_act=2),
        s(f"Zuerst {v['w2']} danach {v['w3']}.", v["a2"] + v["a3"], min_act=2),
        s(f"{v['w4']} und zum Schluss {v['w5']}.", v["a4"] + v["a5"], min_act=2),
    ]
    if trade == "GaLaBau":
        items += [
            s(
                "60 Quadratmeter Pflaster verlegt 25 laufende Meter Rasenkantensteine gesetzt Hecke geschnitten.",
                ("Pflaster verlegt", "Rasenkantensteine", "Hecke"),
                min_act=3,
            ),
            s(
                "heute ich hab gemacht 15 meter palisaden gesetzt und 30 quadrat rollrasen verlegt.",
                ("Palisaden", "Rasen verlegt"),
                min_act=2,
            ),
            s("40 m² Keramikterrasse verlegt Gehweg Pflaster verlegt.", ("Keramikterrasse", "Pflaster"), min_act=2),
        ]
    elif trade == "Tiefbau":
        items += [
            s(
                "Mit Bagger Graben ausgehoben 20 lfm KG-Rohre verlegt Graben verfüllt Planum verdichtet.",
                ("Graben ausgehoben", "KG-Rohre", "Graben verfüllt", "Untergrund verdichtet"),
                min_act=3,
            ),
            s(
                "Kanal angeschlossen Schacht gesetzt Straße aufgemacht Asphalt eingebaut.",
                ("Kanal", "Asphalt eingebaut"),
                min_act=2,
            ),
            s("50 Meter Graben verfüllt Splitt eingebaut Untergrund verdichtet.", ("Graben verfüllt", "Splitt"), min_act=2),
        ]
    else:
        items += [
            s(
                "15 lfm Asphalt geschnitten dann 30 qm asphaltiert danach 30 qm Pflaster verlegt und 15 lfm Rasenkantensteine gesetzt.",
                ("Asphalt schneiden", "Asphalt eingebaut", "Pflaster verlegt", "Rasenkantensteine"),
                min_act=3,
            ),
            s(
                "Öffentliche Fläche: Schotter eingebaut Pflaster verlegt Borde gesetzt Hecke zurückgeschnitten.",
                ("Schotter", "Pflaster", "Borde"),
                min_act=3,
            ),
            s(
                "Graben für Wasserleitung ausgehoben KG-Rohre verlegt Straße asphaltiert 18 m².",
                ("Graben ausgehoben", "KG-Rohre", "Asphalt eingebaut"),
                min_act=3,
            ),
            s(
                "Parkplatz Frostschutz eingebaut Asphalt eingebaut Rasenkantensteine gesetzt.",
                ("Frostschutz", "Asphalt eingebaut", "Rasenkantensteine"),
                min_act=2,
            ),
        ]
    return items


def _broken_and_short(v: dict, trade: str) -> list[dict]:
    work = v["w2"] if trade != "Strassenbau" else "11 meter asphalt schneiden und 24 quadrat asphaltiert"
    return [
        s(f"heute {work} problem regen offen rest morgen kunde zufrieden", ("Asphalt schneiden", "Asphalt eingebaut") if trade == "Strassenbau" else v["a2"], problem=True, open_=True, customer=True, min_act=1),
        s(f"heute auf baustelle {v['w3']} fertig", v["a3"], min_act=1),
        s(f"{v['w5']} bauherr kurz da", v["a5"], customer=True, min_act=1),
        s("Pflaster gemacht.", ("Pflaster",), min_act=1) if trade == "GaLaBau" else s("Graben gemacht.", ("Graben",), min_act=1),
        s("Asphalt fertig.", ("Asphalt eingebaut",), min_act=1) if trade == "Strassenbau" else s("Schotter reingemacht.", ("Schotter",), min_act=1),
        s(f"heute ich hab gemacht {v['w4']}", v["a4"], min_act=1),
    ]


def _mega_and_long(v: dict) -> list[dict]:
    raw = (
        f"Heute haben wir zuerst {v['w1']} dann {v['w2']} "
        f"danach {v['rain']} {v['open']} {v['cust']} Problem Lieferung spät Offen Rest Montag."
    )
    long_chain = (
        f"Morgens um sechs angefangen mit {v['w3']} im Anschluss {v['w4']} "
        f"zwischendurch {v['cust2']} leider {v['rain2']} "
        f"dementsprechend {v['plan']} {v['open_exp']}."
    )
    return [
        s(raw, v["a1"], problem=True, open_=True, customer=True, min_act=2),
        s(long_chain, v["a3"] + v["a4"], problem=True, open_=True, customer=True, min_act=2),
        s(f"Ja also vom Tag her {v['w1']} und also {v['w5']} und Feierabend.", v["a1"], min_act=1),
    ]


def _qty_pad(v: dict, trade: str, count: int) -> list[dict]:
    tails = [
        ("", False, False, False),
        (" leider Regen abbrechen morgen weiter.", True, True, False),
        (" Bauherr informiert.", False, False, True),
        (" Problem Wetter Offen nächste Woche.", True, True, False),
    ]
    out: list[dict] = []
    if trade == "GaLaBau":
        def raw_at(q: int, i: int) -> tuple[str, tuple[str, ...]]:
            opts = (
                (f"{q} Quadratmeter Pflaster verlegt.", ("Pflaster",)),
                (f"{q} laufende Meter Hecke geschnitten.", ("Hecke",)),
                (f"{q} Kubikmeter Schotter eingebaut.", ("Schotter",)),
            )
            return opts[i % len(opts)]
        start, step = 12, 3
    elif trade == "Tiefbau":
        def raw_at(q: int, i: int) -> tuple[str, tuple[str, ...]]:
            opts = (
                (f"{q} laufende Meter Graben ausgehoben.", ("Graben ausgehoben",)),
                (f"{q} Meter KG-Rohre verlegt.", ("KG-Rohre",)),
                (f"{q} Kubikmeter Frostschutz eingebaut.", ("Frostschutz",)),
            )
            return opts[i % len(opts)]
        start, step = 8, 2
    else:
        def raw_at(q: int, i: int) -> tuple[str, tuple[str, ...]]:
            opts = (
                (f"{q} lfm Asphalt schneiden.", ("Asphalt schneiden",)),
                (f"{q} Quadratmeter asphaltiert.", ("Asphalt eingebaut",)),
                (f"{q} m² Pflaster verlegt.", ("Pflaster",)),
            )
            return opts[i % len(opts)]
        start, step = 10, 2
    i = 0
    q = start
    while len(out) < count:
        raw_tpl, acts = raw_at(q, i)
        tail, prob, opn, cust = tails[i % len(tails)]
        out.append(
            s(
                raw_tpl + tail,
                acts,
                problem=prob,
                open_=opn,
                customer=cust,
                min_act=1,
            )
        )
        i += 1
        if i % 3 == 0:
            q += step
    return out


def build_trade(trade: str) -> list[dict]:
    v = VOCAB[trade]
    items: list[dict] = []
    items += _core_live(v, trade)
    items += _explicit_p23(v)
    items += _chains(v, trade)
    items += _broken_and_short(v, trade)
    items += _mega_and_long(v)
    need = TARGET_PER_TRADE - len(items)
    items += _qty_pad(v, trade, max(need, 1))
    return items[:TARGET_PER_TRADE]


def main() -> None:
    lines = [
        '"""Pilot-Welle 29 — 100 Basisszenarien pro Gewerk: GaLaBau, Tiefbau, Straßenbau (generiert)."""',
        "from __future__ import annotations",
        "from typing import Any, Iterator",
        f"TRADES = {TRADES!r}",
        "TRADE_SCENARIOS: dict[str, list[dict[str, Any]]] = {",
    ]
    for trade in TRADES:
        scenarios = build_trade(trade)
        assert len(scenarios) == TARGET_PER_TRADE, (trade, len(scenarios))
        lines.append(f'    "{trade}": [')
        for spec in scenarios:
            lines.append(f"        {spec!r},")
        lines.append("    ],")
    lines += [
        "}",
        "",
        "def all_base_scenarios() -> Iterator[tuple[str, dict[str, Any]]]:",
        "    for trade in TRADES:",
        "        for spec in TRADE_SCENARIOS[trade]:",
        "            yield trade, spec",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} — {len(TRADES) * TARGET_PER_TRADE} scenarios")


if __name__ == "__main__":
    main()
