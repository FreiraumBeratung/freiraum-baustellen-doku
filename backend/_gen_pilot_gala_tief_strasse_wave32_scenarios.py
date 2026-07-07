"""Generator Pilot-Welle 32 — PANZEK-Tagesstunden-Sphäre (150 gesamt).

Abgestimmt auf echte Pilot-Berichte: Graben/Kabel/Rohre, Planum, Drainage,
Asphalt/Pflaster, Entsorgung, LKW-Ladungen, Bagger/Radlader/LKW-Stunden.
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).parent / "pilot_gala_tief_strasse_wave32_scenarios.py"
TRADES = ("GaLaBau", "Tiefbau", "Strassenbau")
TARGET_PER_TRADE = 50


def s(raw: str, acts: tuple[str, ...], **kw) -> dict:
    d = dict(
        raw=raw,
        acts=acts,
        mats=(),
        mach=(),
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
        w1="75 Quadratmeter Pflaster legen 150 laufende Meter Bankette bauen",
        w2="Vorbereitung für Pflaster 90 Meter Schotter eingebaut Untergrund verdichtet",
        w3="dreiteilige Rinne gesetzt Schotter Planum erstellt",
        w4="Akku Rinne gesetzt Fallrohre angeschlossen zwei Stunden",
        w5="22 Quadratmeter Hofpflaster verlegt 8 laufende Meter Randsteine gesetzt",
        rain="leider mussten wir wegen Regen abbrechen",
        rain2="Problem Radlader defekt mussten stoppen",
        uneben="Untergrund war sehr uneben was zu Problemen geführt hat",
        open="morgen müssen wir noch die Bankette fertig machen",
        open2="morgen müssen wir noch die Rinne abschließen",
        plan="dementsprechend machen wir morgen den Rest fertig",
        cust="der Kunde war sehr zufrieden",
        cust2="mit der Bauleitung kurz gesprochen Termin abgestimmt",
        prob="Problem Splitt Lieferung zu spät",
        open_exp="Offen Abschluss Freitag",
        a1=("Pflaster verlegt", "Bankette"),
        a2=("Schotter", "Untergrund verdichtet"),
        a3=("Rinne", "Planum"),
        a4=("Rinne",),
        a5=("Pflaster verlegt",),
        mat_ent=("Boden entsorgt",),
        mat_sch=("Schotter",),
        mach_br=("Bagger", "Radlader"),
    ),
    "Tiefbau": dict(
        w1="Graben ziehen ca 45 Meter Kabel ziehen 245 Meter Rohre legen DN 160 und DN 125",
        w2="Graben zumachen 215 Meter Wasserleitung eingesandet Graben verfüllt",
        w3="Erdplanum erstellt Schotterplanum erstellt Drainage erstellt",
        w4="Raketen suchen bis Mittag Graben verfüllen Stemmarbeiten",
        w5="Wand abdichtet Noppenbahn verlegt 34 Meter Drainagerohr verlegt",
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
        a1=("Graben ausgehoben", "Kabel", "Rohr"),
        a2=("Graben verfüllt",),
        a3=("Erdplanum", "Schotterplanum", "Drainage"),
        a4=("Graben verfüllt",),
        a5=("Abdichtung", "Drainage"),
        mat_ent=("Boden entsorgt", "Bauschutt entsorgt"),
        mat_lkw=("LKW",),
        mach_all=("Bagger", "Radlader", "LKW"),
    ),
    "Strassenbau": dict(
        w1="35,50 laufende Meter Asphalt schneiden Merkstein setzen 2 Stück Bodenarbeiten",
        w2="45 Quadratmeter asphaltieren 7,75 Quadratmeter Pflaster legen Baustelle aufräumen",
        w3="Graben verfüllen und vorbereiten für Asphalt Einbau",
        w4="150 laufende Meter Bankette bauen 6 Meter Asphalt schneiden",
        w5="25 Quadratmeter asphaltiert 60 Meter TOK-Band verlegt",
        rain="Problem Verdichtung nicht möglich mussten abbrechen",
        rain2="leider Bagger defekt mussten stoppen",
        uneben="Problem Tragschicht zu weich",
        open="Offen Fuge morgen",
        open2="morgen müssen wir noch die Markierung machen",
        plan="dementsprechend asphaltieren wir morgen weiter",
        cust="Stadt informiert Kundengespräch lief gut",
        cust2="Bauleitung kurz da",
        prob="Problem Absperrung fehlt",
        open_exp="Offen Gehweg Freitag",
        a1=("Asphalt schneiden",),
        a2=("Asphalt eingebaut", "Pflaster verlegt"),
        a3=("Graben verfüllt",),
        a4=("Bankette", "Asphalt schneiden"),
        a5=("Asphalt eingebaut",),
        mat_asp=("Asphalt",),
        mat_tok=("TOK",),
        mat_ent=("Asphalt entsorgt",),
        mach_bl=("Bagger", "LKW"),
    ),
}


def _material_block(v: dict, trade: str) -> str:
    if trade == "GaLaBau":
        return "15 ton Boden entsorgt 40 ton Schotter 0/45 eingebaut."
    if trade == "Tiefbau":
        return (
            "108 ton Bauschutt entsorgt 6 LKW HT Bodenaushub 22 ton Boden entsorgt "
            "Bagger 9 std Radlader 3 std LKW 4 std."
        )
    return (
        "7 ton Asphalt 0/11 eingebaut 35 Meter TOK-Band 9,3 ton Asphalt entsorgt "
        "Bagger 5 std LKW 3 std."
    )


def _core_live(v: dict, trade: str) -> list[dict]:
    return [
        s(f"Vormittag Waltringen {v['w1']} {v['rain']} {v['open']} {v['cust']}.", v["a1"], problem=True, open_=True, customer=True, min_act=1),
        s(f"{v['w2']} {v['rain2']}.", v["a2"], problem=True, min_act=1),
        s(f"Bremke Feuerwehrhaus {v['w3']} {v['uneben']} {v['cust2']}.", v["a3"], problem=True, customer=True, min_act=1),
        s(f"{v['w4']} {v['open2']}.", v["a4"], open_=True, min_act=1),
        s(f"{v['w5']} {v['prob']} {v['open_exp']}.", v["a5"], problem=True, open_=True, min_act=1),
        s(f"{v['w1']} {v['plan']}.", v["a1"], open_=True, min_act=1),
        s(f"{v['w2']} {v['cust']}.", v["a2"], customer=True, min_act=1),
        s(f"Heute nur {v['cust2']} wegen Termin keine Arbeit wegen Regen.", (), problem=True, customer=True, min_act=0),
    ]


def _explicit_p23(v: dict, trade: str) -> list[dict]:
    return [
        s(f"{v['w3']} Problem Material knapp Offen Rest morgen.", v["a3"], problem=True, open_=True, min_act=1),
        s(f"{v['w2']} Problem Lieferung fehlt Offen nächste Woche.", v["a2"], problem=True, open_=True, min_act=1),
        s(f"{v['w1']} leider mussten wir abbrechen morgen weiter.", v["a1"], problem=True, open_=True, min_act=1),
        s(f"{v['w5']} Kundengespräch mit Bauleitung Abstimmung Termin.", v["a5"], customer=True, min_act=1),
        s("Problem Motorsäge defekt Offen Ersatz morgen.", (), problem=True, open_=True, min_act=0),
        s(f"{v['w4']} Bauherr zufrieden.", v["a4"], customer=True, min_act=1),
    ]


def _chains(v: dict, trade: str) -> list[dict]:
    mach = v.get("mach_all") or v.get("mach_br") or v.get("mach_bl") or ()
    items = [
        s(v["w1"], v["a1"], min_act=1),
        s(f"Erst {v['w2']} dann {v['w3']}.", v["a2"] + v["a3"], min_act=2),
        s(f"{v['w4']} und am Ende {v['w5']}.", v["a4"] + v["a5"], min_act=2),
    ]
    if trade == "GaLaBau":
        items += [
            s(
                "Pflaster legen ca 75 m2 Bankette bauen ca 150 Meter Boden entsorgt 15 ton "
                "Bagger 8 std Radlader 2,5 std LKW 3 std.",
                ("Pflaster verlegt", "Bankette"),
                mats=("Boden entsorgt",),
                mach=("Bagger", "Radlader", "LKW"),
                min_act=2,
            ),
            s(
                "dreiteilige Rinne gesetzt Schotter Planum erstellt 40 ton 0/45 Zementmörtel 6 Sack.",
                ("Rinne", "Planum"),
                mats=("Schotter",),
                min_act=1,
            ),
            s(
                "Hofeinfahrt 18 m2 Pflaster verlegt Randsteine gesetzt Laub gehäckselt.",
                ("Pflaster verlegt", "Randstein", "Laub"),
                min_act=2,
            ),
        ]
    elif trade == "Tiefbau":
        items += [
            s(
                "Graben ziehen ca 10 Meter ein Kopfloch Asphalt schneiden 6 Meter Graben zumachen 15 Meter "
                "Bagger 7 std.",
                ("Graben ausgehoben", "Asphalt schneiden", "Graben verfüllt"),
                mach=("Bagger",),
                min_act=2,
            ),
            s(
                "Erdplanum Schotterplanum Drainage erstellt 6 LKW HT Bodenaushub 1 LKW HT Tragschicht "
                "4 Kubikmeter Betonaushub Bagger 9 std Radlader 2 std LKW 8 std.",
                ("Erdplanum", "Schotterplanum", "Drainage"),
                mats=("LKW",),
                mach=("Bagger", "Radlader", "LKW"),
                min_act=2,
            ),
            s(
                "Wasserleitung eingesandet Schotter Planum erstellt Fallrohre angeschlossen Stemmarbeiten "
                "Bagger 3 std Radlader 0,5 std Bagger 3,5t 7 std.",
                ("Wasserleitung", "Planum", "Fallrohr"),
                mach=("Bagger", "Radlader"),
                min_act=2,
            ),
            s(
                "34 Meter Drainagerohr 1 Rolle Noppenbahn 1 Rolle Vlies 2 Eimer Dickbeschichtung verarbeitet.",
                ("Drainage", "Abdichtung"),
                mats=("Drainage", "Vlies"),
                min_act=1,
            ),
        ]
    else:
        items += [
            s(
                "Asphalt schneiden dann 22 qm asphaltiert danach 18 qm Pflaster legen Randsteine gesetzt "
                "7 ton Asphalt 0/11 22 Meter TOK-Band Bagger 1 std LKW 4 std.",
                ("Asphalt schneiden", "Asphalt eingebaut", "Pflaster verlegt"),
                mats=("Asphalt", "TOK"),
                mach=("Bagger", "LKW"),
                min_act=2,
            ),
            s(
                "Graben verfüllen Vorbereitung für Asphalt 15 ton Schotter Boden entsorgt 7,2 ton "
                "Bagger 6 std LKW 2,5 std.",
                ("Graben verfüllt",),
                mats=("Schotter", "Boden entsorgt"),
                mach=("Bagger", "LKW"),
                min_act=1,
            ),
            s(
                "10 kV Ense Waltringen Asphalt schneiden 35 Meter Merkstein setzen Bodenarbeiten "
                "9,3 ton Asphalt entsorgt.",
                ("Asphalt schneiden", "Merkstein"),
                mats=("Asphalt entsorgt",),
                min_act=1,
            ),
            s(
                "Asphaltieren 25 m2 6,5 ton Asphalt 0/11 60 Meter TOK-Band Bagger 3,5 std.",
                ("Asphalt eingebaut",),
                mats=("Asphalt", "TOK"),
                mach=("Bagger",),
                min_act=1,
            ),
        ]
    return items


def _broken_and_short(v: dict, trade: str) -> list[dict]:
    if trade == "Strassenbau":
        work = "9 meter asphalt schneiden und 20 quadrat asphaltiert"
        acts = ("Asphalt schneiden", "Asphalt eingebaut")
    elif trade == "Tiefbau":
        work = "graben ziehen 40 meter rohre legen"
        acts = ("Graben ausgehoben", "Rohr")
    else:
        work = "pflaster legen 30 m2 bankette"
        acts = ("Pflaster verlegt", "Bankette")
    return [
        s(
            f"heute {work} problem regen offen rest morgen kunde zufrieden bagger 4 std",
            acts,
            mach=("Bagger",),
            problem=True,
            open_=True,
            customer=True,
            min_act=1,
        ),
        s(f"heute auf baustelle {v['w3']} fertig", v["a3"], min_act=1),
        s(f"{v['w5']} bauherr kurz da", v["a5"], customer=True, min_act=1),
        s("Rinne gesetzt.", ("Rinne",), min_act=1) if trade == "GaLaBau" else s("Erdplanum fertig.", ("Erdplanum",), min_act=1),
        s("Asphalt fertig.", ("Asphalt eingebaut",), min_act=1) if trade == "Strassenbau" else s("Drainage fertig.", ("Drainage",), min_act=1),
        s(f"heute ich hab gemacht {v['w4']}", v["a4"], min_act=1),
    ]


def _mega_and_long(v: dict, trade: str) -> list[dict]:
    raw = (
        f"Heute Waltringen Ense zuerst {v['w1']} dann {v['w2']} "
        f"{v['rain']} {v['open']} {v['cust']} Problem Lieferung spät Offen Rest Dienstag."
    )
    long_chain = (
        f"Morgens um sechs angefangen mit {v['w3']} im Anschluss {v['w4']} "
        f"zwischendurch {v['cust2']} leider {v['rain2']} "
        f"dementsprechend {v['plan']} {v['open_exp']}."
    )
    long_acts = v["a3"] + (v["a4"][:1] if v["a4"] else ())
    return [
        s(raw, v["a1"], problem=True, open_=True, customer=True, min_act=1),
        s(long_chain, long_acts, problem=True, open_=True, customer=True, min_act=1),
        s(f"Ja also vom Tagher {v['w1']} und also {v['w5']} und Feierabend.", v["a1"], min_act=1),
    ]


def _qty_pad(v: dict, trade: str, count: int) -> list[dict]:
    tails = [
        ("", False, False, False, ()),
        (" leider Regen abbrechen morgen weiter.", True, True, False, ()),
        (" Bauherr informiert.", False, False, True, ()),
        (" Problem Wetter Offen nächste Woche. Bagger 5 std.", True, True, False, ("Bagger",)),
    ]
    out: list[dict] = []
    if trade == "GaLaBau":
        def raw_at(q: int, i: int) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
            opts = (
                (f"{q} Quadratmeter Pflaster legen Bankette {q+20} Meter.", ("Pflaster verlegt", "Bankette"), ()),
                (f"{q} laufende Meter Rinne gesetzt Schotter Planum.", ("Rinne", "Planum"), ("Schotter",)),
                (f"{q} ton Boden entsorgt Radlader {2 + i % 3} std.", (), ("Boden entsorgt",)),
            )
            return opts[i % len(opts)]

        start, step = 12, 4
    elif trade == "Tiefbau":
        def raw_at(q: int, i: int) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
            opts = (
                (f"Graben ziehen ca {q} Meter Kabel ziehen {q*5} Meter.", ("Graben ausgehoben", "Kabel"), ()),
                (f"{q} Meter Drainagerohr verlegt Noppenbahn verlegt.", ("Drainage",), ("Drainage",)),
                (f"{q} LKW HT Bodenaushub {max(1, q // 2)} ton Bauschutt entsorgt Bagger {4 + i % 4} std.", (), ("LKW", "Bauschutt entsorgt")),
            )
            return opts[i % len(opts)]

        start, step = 8, 3
    else:
        def raw_at(q: int, i: int) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
            opts = (
                (f"{q} lfm Asphalt schneiden {q//2} ton Asphalt entsorgt.", ("Asphalt schneiden",), ("Asphalt entsorgt",)),
                (f"{q} Quadratmeter asphaltieren {q} Meter TOK-Band LKW {3+i%3} std.", ("Asphalt eingebaut",), ("Asphalt", "TOK")),
                (f"{q} m2 Pflaster legen {q//3} ton Schotter Bagger {2+i%3} std.", ("Pflaster verlegt",), ("Schotter",)),
            )
            return opts[i % len(opts)]

        start, step = 10, 3
    i = 0
    q = start
    while len(out) < count:
        raw_tpl, acts, mats = raw_at(q, i)
        tail, prob, opn, cust, mach = tails[i % len(tails)]
        out.append(
            s(
                raw_tpl + tail,
                acts,
                mats=mats,
                mach=mach or (("Radlader",) if "radlader" in raw_tpl.casefold() else ()),
                problem=prob,
                open_=opn,
                customer=cust,
                min_act=0 if not acts else 1,
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
    items += _explicit_p23(v, trade)
    items += _chains(v, trade)
    items += _broken_and_short(v, trade)
    items += _mega_and_long(v, trade)
    need = TARGET_PER_TRADE - len(items)
    items += _qty_pad(v, trade, max(need, 1))
    return items[:TARGET_PER_TRADE]


def main() -> None:
    lines = [
        '"""Pilot-Welle 32 — PANZEK-Sphäre: 50 Basisszenarien pro Gewerk (generiert)."""',
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
