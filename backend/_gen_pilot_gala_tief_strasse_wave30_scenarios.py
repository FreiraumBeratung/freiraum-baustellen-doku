"""Generator Pilot-Welle 30 — 100 Szenarien × GaLaBau, Tiefbau, Straßenbau (300 gesamt).

Komplett neue Fälle gegenüber Welle 29, gleiche Struktur/Sphäre.
Einmal ausführen: python _gen_pilot_gala_tief_strasse_wave30_scenarios.py
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).parent / "pilot_gala_tief_strasse_wave30_scenarios.py"
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
        w1="35 Quadratmeter Natursteinpflaster verlegt und 8 laufende Meter Bordsteine gesetzt",
        w2="22 Quadratmeter WPC-Terrasse gebaut einen Kubikmeter Kies eingebaut",
        w3="Hecken geschnitten Kompost eingearbeitet",
        w4="45 Quadratmeter Mährasen verlegt Sichtschutzzaun gesetzt",
        w5="Beet angelegt Laub gehäckselt",
        rain="leider mussten wir stoppen weil es stark geregnet hat",
        rain2="wir mussten abbrechen weil der Kleber bei Hitze zu schnell abbindet",
        uneben="leider war die Wand nicht lotrecht was zu Problemen geführt hat",
        open="morgen müssen wir noch die letzten drei Steine setzen",
        open2="morgen müssen wir noch den Zaun fertig machen",
        plan="dementsprechend machen wir morgen den Rest fertig",
        cust="der Kunde war sehr zufrieden",
        cust2="mit der Kundin kurz gesprochen sie ist einverstanden",
        prob="Problem Splitt zu spät geliefert",
        open_exp="Offen Abschluss Donnerstag",
        a1=("Pflaster verlegt", "Randstein"),
        a2=("WPC", "Kies"),
        a3=("Hecke geschnitten", "Kompost"),
        a4=("Rasen verlegt", "Zaun"),
        a5=("Beet", "Laub"),
        mats=(),
    ),
    "Tiefbau": dict(
        w1="18 laufende Meter Fundamentgraben ausgehoben HT-Rohr DN 125 verlegt Graben verfüllt",
        w2="vier Kubikmeter Sand eingebaut und verdichtet Planum hergestellt",
        w3="Frostschutz eingebaut Schottertragschicht hergestellt",
        w4="Kanalisation angeschlossen Revisionsschacht gesetzt",
        w5="Drainage verlegt Filtervlies eingebaut",
        rain="mussten abbrechen weil Pressfitting fehlt",
        rain2="leider mussten wir wegen Staub stoppen",
        uneben="Problem Anschluss zu eng was zu Problemen geführt hat",
        open="morgen müssen wir noch den Schacht setzen",
        open2="morgen müssen wir noch die Drainage fertig machen",
        plan="dementsprechend verfüllen wir morgen weiter",
        cust="Auftraggeber kurz informiert",
        cust2="Mit dem Bauherr abgestimmt",
        prob="Problem Dichtung undicht",
        open_exp="Offen Schacht morgen",
        a1=("Graben ausgehoben", "HT-Rohre", "Graben verfüllt"),
        a2=("Sand eingebaut", "Planum"),
        a3=("Frostschutz", "Schottertragschicht"),
        a4=("Kanal", "Schacht"),
        a5=("Drainage", "Geotextil"),
        mats=(),
    ),
    "Strassenbau": dict(
        w1="12 laufende Meter Asphalt geschnitten 22 Quadratmeter asphaltiert 18 Quadratmeter Gehwegpflaster verlegt 10 laufende Meter Bordsteine gesetzt",
        w2="Straßenaufbruch ausgehoben 9 Meter Asphalt schneiden 20 Quadratmeter asphaltiert",
        w3="Frostschutz eingebaut Splitt eingebaut Untergrund verdichtet Asphalt eingebaut",
        w4="Tiefbord gesetzt Muldensteine verlegt Einlauf gesetzt",
        w5="Belag abgefräst 16 Quadratmeter Asphalt asphaltiert",
        rain="Problem Verdichtung nicht möglich mussten abbrechen",
        rain2="leider Bagger defekt mussten stoppen",
        uneben="Problem Tragschicht zu weich",
        open="Offen Fuge morgen",
        open2="morgen müssen wir noch die Markierung machen",
        plan="dementsprechend fräsen wir morgen weiter",
        cust="Stadt informiert Kundengespräch lief gut",
        cust2="Bauleitung kurz da",
        prob="Problem Absperrung fehlt",
        open_exp="Offen Gehweg Freitag",
        a1=("Asphalt schneiden", "Asphalt eingebaut", "Pflaster verlegt", "Randstein"),
        a2=("Graben ausgehoben", "Asphalt schneiden", "Asphalt eingebaut"),
        a3=("Frostschutz", "Splitt", "Asphalt eingebaut"),
        a4=("Borde gesetzt", "Rinnensteine", "Straßenabläufe"),
        a5=("Asphalt eingebaut",),
        mats=(),
    ),
}


def _core_live(v: dict, trade: str) -> list[dict]:
    return [
        s(f"Vormittag {v['w1']} {v['rain']} {v['open']} {v['cust']}.", v["a1"], problem=True, open_=True, customer=True, min_act=2),
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
        s("Problem Motorsäge defekt Offen Ersatz morgen.", (), problem=True, open_=True, min_act=0),
        s(f"{v['w4']} Bauherr zufrieden.", v["a4"], customer=True, min_act=1),
    ]


def _chains(v: dict, trade: str) -> list[dict]:
    items = [
        s(v["w1"], v["a1"], min_act=2),
        s(f"Erst {v['w2']} dann {v['w3']}.", v["a2"] + v["a3"], min_act=2),
        s(f"{v['w4']} und am Ende {v['w5']}.", v["a4"] + v["a5"], min_act=2),
    ]
    if trade == "GaLaBau":
        items += [
            s(
                "55 Quadratmeter Natursteinpflaster verlegt 18 laufende Meter Bordsteine gesetzt Hecken geschnitten.",
                ("Pflaster verlegt", "Randstein", "Hecke"),
                min_act=2,
            ),
            s(
                "heute ich hab gemacht 12 meter sichtschutzzaun gesetzt und 28 quadrat mährasen verlegt.",
                ("Zaun", "Rasen verlegt"),
                min_act=2,
            ),
            s("32 m² Feinsteinzeugplatten verlegt Einfahrt Pflaster verlegt.", ("Feinsteinzeug", "Pflaster"), min_act=2),
        ]
    elif trade == "Tiefbau":
        items += [
            s(
                "Mit Minibagger Fundamentgraben ausgehoben 16 lfm HT-Rohr verlegt Graben verfüllt Untergrund verdichtet.",
                ("Graben ausgehoben", "HT-Rohre", "Graben verfüllt", "Untergrund verdichtet"),
                min_act=3,
            ),
            s(
                "Hausanschluss Kanal angeschlossen Schacht gesetzt Straße aufgemacht Asphalt eingebaut.",
                ("Kanal", "Schacht", "Asphalt eingebaut"),
                min_act=2,
            ),
            s("40 Meter Graben verfüllt Splitt eingebaut Untergrund verdichtet.", ("Graben verfüllt", "Splitt"), min_act=2),
        ]
    else:
        items += [
            s(
                "12 lfm Asphalt geschnitten dann 22 qm asphaltiert danach 18 qm Gehwegpflaster verlegt und 10 lfm Bordsteine gesetzt.",
                ("Asphalt schneiden", "Asphalt eingebaut", "Pflaster verlegt", "Randstein"),
                min_act=3,
            ),
            s(
                "Bushaltestelle: Splitt eingebaut Pflaster verlegt Borde gesetzt Hecke zurückgeschnitten.",
                ("Splitt", "Pflaster", "Borde"),
                min_act=3,
            ),
            s(
                "Graben für Gasleitung ausgehoben KG-Rohre verlegt Straße asphaltiert 14 m².",
                ("Graben ausgehoben", "KG-Rohre", "Asphalt eingebaut"),
                min_act=3,
            ),
            s(
                "Hofeinfahrt Frostschutz eingebaut Asphalt eingebaut Bordsteine gesetzt.",
                ("Frostschutz", "Asphalt eingebaut", "Randstein"),
                min_act=2,
            ),
        ]
    return items


def _broken_and_short(v: dict, trade: str) -> list[dict]:
    work = v["w2"] if trade != "Strassenbau" else "9 meter asphalt schneiden und 20 quadrat asphaltiert"
    return [
        s(
            f"heute {work} problem regen offen rest morgen kunde zufrieden",
            ("Asphalt schneiden", "Asphalt eingebaut") if trade == "Strassenbau" else v["a2"],
            problem=True,
            open_=True,
            customer=True,
            min_act=1,
        ),
        s(f"heute auf baustelle {v['w3']} fertig", v["a3"], min_act=1),
        s(f"{v['w5']} bauherr kurz da", v["a5"], customer=True, min_act=1),
        s("Beet gemacht.", ("Beet",), min_act=1) if trade == "GaLaBau" else s("Fundamentgraben gemacht.", ("Graben",), min_act=1),
        s("Asphalt fertig.", ("Asphalt eingebaut",), min_act=1) if trade == "Strassenbau" else s("Sand reingemacht.", ("Sand",), min_act=1),
        s(f"heute ich hab gemacht {v['w4']}", v["a4"], min_act=1),
    ]


def _mega_and_long(v: dict, trade: str) -> list[dict]:
    raw = (
        f"Heute haben wir zuerst {v['w1']} dann {v['w2']} "
        f"danach {v['rain']} {v['open']} {v['cust']} Problem Lieferung spät Offen Rest Dienstag."
    )
    long_chain = (
        f"Morgens um sieben angefangen mit {v['w3']} im Anschluss {v['w4']} "
        f"zwischendurch {v['cust2']} leider {v['rain2']} "
        f"dementsprechend {v['plan']} {v['open_exp']}."
    )
    long_acts = v["a3"] + (("Zaun",) if trade == "GaLaBau" else v["a4"])
    return [
        s(raw, v["a1"], problem=True, open_=True, customer=True, min_act=2),
        s(long_chain, long_acts, problem=True, open_=True, customer=True, min_act=2),
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
                (f"{q} Quadratmeter Natursteinpflaster verlegt.", ("Pflaster",)),
                (f"{q} laufende Meter Hecken geschnitten.", ("Hecke",)),
                (f"{q} Kubikmeter Kies eingebaut.", ("Kies",)),
            )
            return opts[i % len(opts)]

        start, step = 14, 4
    elif trade == "Tiefbau":
        def raw_at(q: int, i: int) -> tuple[str, tuple[str, ...]]:
            opts = (
                (f"{q} laufende Meter Fundamentgraben ausgehoben.", ("Graben ausgehoben",)),
                (f"{q} Meter HT-Rohr verlegt.", ("HT-Rohre",)),
                (f"{q} Kubikmeter Frostschutz eingebaut.", ("Frostschutz",)),
            )
            return opts[i % len(opts)]

        start, step = 9, 3
    else:
        def raw_at(q: int, i: int) -> tuple[str, tuple[str, ...]]:
            opts = (
                (f"{q} lfm Asphalt schneiden.", ("Asphalt schneiden",)),
                (f"{q} Quadratmeter asphaltiert.", ("Asphalt eingebaut",)),
                (f"{q} m² Gehwegpflaster verlegt.", ("Pflaster",)),
            )
            return opts[i % len(opts)]

        start, step = 11, 3
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
    items += _mega_and_long(v, trade)
    need = TARGET_PER_TRADE - len(items)
    items += _qty_pad(v, trade, max(need, 1))
    return items[:TARGET_PER_TRADE]


def main() -> None:
    lines = [
        '"""Pilot-Welle 30 — 100 Basisszenarien pro Gewerk: GaLaBau, Tiefbau, Straßenbau (generiert)."""',
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
