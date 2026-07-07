"""Generator Pilot-Welle 33 — PANZEK-Tagesstunden-Sphäre (300 gesamt).

Welle-33-Variante: gleicher Kern wie W31, andere Texte/Orte/Reihenfolgen.
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).parent / "pilot_gala_tief_strasse_wave33_scenarios.py"
TRADES = ("GaLaBau", "Tiefbau", "Strassenbau")
TARGET_PER_TRADE = 100
SITE_A = "Höxter"
SITE_B = "Borgentreich"
SITE_C = "Brakel"


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
        w1="62 Quadratmeter Pflaster legen 120 laufende Meter Bankette bauen",
        w2="Unterbau vorbereitet 75 Meter Schotter eingebaut Planum verdichtet",
        w3="dreiteilige Rinne gesetzt Schotter Planum erstellt",
        w4="Fallrohre angeschlossen Akku Rinne gesetzt drei Stunden",
        w5="28 Quadratmeter Hofpflaster verlegt 12 laufende Meter Randsteine gesetzt",
        rain="Problem Starkregen mussten wir abbrechen",
        rain2="Problem Bagger hydraulik undicht mussten stoppen",
        uneben="Gefälle stimmte nicht was zu Problemen geführt hat",
        open="Offen Bankette Abschnitt zwei morgen",
        open2="Offen Rinne Anschluss Donnerstag",
        plan="machen wir morgen früh den Rest fertig",
        cust="Bauherr war einverstanden und zufrieden",
        cust2="Auftraggeber kurz informiert Termin abgestimmt",
        prob="Problem Kies Lieferung verspätet",
        open_exp="Offen Fertigstellung nächste Woche",
        a1=("Pflaster verlegt", "Bankette"),
        a2=("Schotter", "Planum"),
        a3=("Rinne", "Planum"),
        a4=("Rinne",),
        a5=("Pflaster verlegt",),
        mat_ent=("Boden entsorgt",),
        mat_sch=("Schotter",),
        mach_br=("Bagger", "Radlader"),
    ),
    "Tiefbau": dict(
        w1="Graben ziehen ca 38 Meter Kabel ziehen 190 Meter Rohre legen DN 110 und DN 160",
        w2="Graben zumachen 180 Meter Wasserleitung eingesandet Graben verfüllt",
        w3="Erdplanum erstellt Schotterplanum erstellt Drainage erstellt",
        w4="Stemmarbeiten bis Mittag danach Graben verfüllen",
        w5="Wand abgedichtet Noppenbahn verlegt 28 Meter Drainagerohr verlegt",
        rain="Problem Pressverbinder fehlte mussten abbrechen",
        rain2="Problem Staubentwicklung mussten wir stoppen",
        uneben="Leitungstrasse zu schmal was zu Problemen geführt hat",
        open="Schacht setzen bleibt offen bis Freitag",
        open2="Offen Drainage Anschluss morgen",
        plan="verfüllen und verdichten wir morgen weiter",
        cust="Bauleitung informiert Termin bestätigt",
        cust2="Mit dem Bauherr Rücksprache gehalten",
        prob="Problem Muffe undicht",
        open_exp="Offen Revisionsschacht Montag",
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
        w1="42 laufende Meter Asphalt schneiden Merkstein setzen 3 Stück Bodenarbeiten",
        w2="38 Quadratmeter asphaltieren 12 Quadratmeter Pflaster legen Baustelle geräumt",
        w3="Graben verfüllen Vorbereitung für Asphalteinbau",
        w4="120 laufende Meter Bankette bauen 8 Meter Asphalt schneiden",
        w5="32 Quadratmeter asphaltiert 55 Meter TOK-Band verlegt",
        rain="Problem Verdichter defekt mussten abbrechen",
        rain2="Problem Walze defekt mussten stoppen",
        uneben="Problem Tragschicht noch zu weich",
        open="Offen Fugenarbeit Mittwoch",
        open2="Offen Markierung und Sperrung morgen",
        plan="asphaltieren und TOK legen wir morgen weiter",
        cust="Stadt Höxter informiert Kundengespräch lief gut",
        cust2="Bauleitung kurz da",
        prob="Problem Verkehrsführung fehlt",
        open_exp="Offen Bushaltestelle Donnerstag",
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
        s(f"Nachmittag {SITE_A} {v['w1']} {v['rain']} {v['open']} {v['cust']}.", v["a1"], problem=True, open_=True, customer=True, min_act=1),
        s(f"{v['w2']} {v['rain2']}.", v["a2"], problem=True, min_act=1),
        s(f"Baustelle {SITE_B} {v['w3']} {v['uneben']} {v['cust2']}.", v["a3"], problem=True, customer=True, min_act=1),
        s(f"{v['w4']} {v['open2']}.", v["a4"], open_=True, min_act=1),
        s(f"{SITE_C} Ortsdurchfahrt {v['w5']} {v['prob']} {v['open_exp']}.", v["a5"], problem=True, open_=True, min_act=1),
        s(f"{v['w1']} {v['open']} {v['plan']}.", v["a1"], open_=True, min_act=1),
        s(f"{v['w2']} {v['cust']}.", v["a2"], customer=True, min_act=1),
        s(f"Heute nur {v['cust2']} wegen Besprechung keine Arbeit wegen Wetter.", (), problem=True, customer=True, min_act=0),
    ]


def _explicit_p23(v: dict, trade: str) -> list[dict]:
    return [
        s(f"{v['w3']} Problem Material knapp Offen Rest morgen.", v["a3"], problem=True, open_=True, min_act=1),
        s(f"{v['w2']} Problem Lieferung fehlt Offen nächste Woche.", v["a2"], problem=True, open_=True, min_act=1),
        s(f"{v['w1']} leider mussten wir abbrechen morgen weiter.", v["a1"], problem=True, open_=True, min_act=1),
        s(f"{v['w5']} Kundengespräch mit Bauleitung Abstimmung Termin.", v["a5"], customer=True, min_act=1),
        s("Problem Kompressor defekt Offen Ersatz übermorgen.", (), problem=True, open_=True, min_act=0),
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
                "Gehweg 24 m2 Pflaster legen Bankette bauen 95 Meter Boden entsorgt 18 ton "
                "Bagger 6 std Radlader 3 std LKW 2 std.",
                ("Pflaster verlegt", "Bankette"),
                mats=("Boden entsorgt",),
                mach=("Bagger", "Radlader", "LKW"),
                min_act=2,
            ),
            s(
                "Rinne gesetzt Schotter Planum erstellt 35 ton Schotter 0/32 Zementmörtel 8 Sack.",
                ("Rinne", "Planum"),
                mats=("Schotter",),
                min_act=1,
            ),
            s(
                "Vorgarten 20 m2 Pflaster verlegt Randsteine gesetzt Laub gehäckselt.",
                ("Pflaster verlegt", "Randstein", "Laub"),
                min_act=2,
            ),
        ]
    elif trade == "Tiefbau":
        items += [
            s(
                "Graben ziehen ca 14 Meter Kopfloch Asphalt schneiden 9 Meter Graben zumachen 22 Meter "
                "Bagger 5,5 std.",
                ("Graben ausgehoben", "Asphalt schneiden", "Graben verfüllt"),
                mach=("Bagger",),
                min_act=2,
            ),
            s(
                "Erdplanum Schotterplanum Drainage erstellt 5 LKW HT Bodenaushub 2 LKW UP Tragschicht "
                "3 Kubikmeter Betonaushub Bagger 8 std Radlader 2,5 std LKW 6 std.",
                ("Erdplanum", "Schotterplanum", "Drainage"),
                mats=("LKW",),
                mach=("Bagger", "Radlader", "LKW"),
                min_act=2,
            ),
            s(
                "Wasserleitung eingesandet Schotter Planum erstellt Fallrohre angeschlossen Stemmarbeiten "
                "Bagger 4 std Radlader 1 std LKW 2 std.",
                ("Wasserleitung", "Planum", "Fallrohr"),
                mach=("Bagger", "Radlader", "LKW"),
                min_act=2,
            ),
            s(
                "28 Meter Drainagerohr 2 Rollen Noppenbahn 1 Rolle Vlies 3 Eimer Dickbeschichtung verarbeitet.",
                ("Drainage", "Abdichtung"),
                mats=("Drainage", "Vlies"),
                min_act=1,
            ),
        ]
    else:
        items += [
            s(
                "Zuerst 18 qm asphaltiert danach 14 qm Pflaster legen Randsteine gesetzt "
                "6 ton Asphalt 0/11 28 Meter TOK-Band Bagger 2 std LKW 3 std.",
                ("Asphalt eingebaut", "Pflaster verlegt"),
                mats=("Asphalt", "TOK"),
                mach=("Bagger", "LKW"),
                min_act=2,
            ),
            s(
                "Graben verfüllen Asphaltvorbereitung 12 ton Schotter Boden entsorgt 5,8 ton "
                "Bagger 5 std LKW 3 std.",
                ("Graben verfüllt",),
                mats=("Schotter", "Boden entsorgt"),
                mach=("Bagger", "LKW"),
                min_act=1,
            ),
            s(
                f"Ortskern {SITE_A} Asphalt schneiden 28 Meter Merkstein setzen Bodenarbeiten "
                "7,5 ton Asphalt entsorgt.",
                ("Asphalt schneiden", "Merkstein"),
                mats=("Asphalt entsorgt",),
                min_act=1,
            ),
            s(
                "Asphaltieren 30 m2 5,5 ton Asphalt 0/11 48 Meter TOK-Band Radlader 2 std.",
                ("Asphalt eingebaut",),
                mats=("Asphalt", "TOK"),
                mach=("Radlader",),
                min_act=1,
            ),
        ]
    return items


def _broken_and_short(v: dict, trade: str) -> list[dict]:
    if trade == "Strassenbau":
        work = "12 meter asphalt schneiden und 16 quadrat asphaltiert"
        acts = ("Asphalt schneiden", "Asphalt eingebaut")
    elif trade == "Tiefbau":
        work = "graben ziehen 35 meter kabel ziehen 120 meter"
        acts = ("Graben ausgehoben", "Kabel")
    else:
        work = "pflaster legen 22 m2 bankette 40 meter"
        acts = ("Pflaster verlegt", "Bankette")
    return [
        s(
            f"heute {work} problem material offen rest dienstag kunde zufrieden bagger 3 std",
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
        f"Heute {SITE_A} und {SITE_B} zuerst {v['w1']} danach {v['w2']} "
        f"{v['rain']} {v['open']} {v['cust']} Problem Lieferant zu spät Offen Rest Donnerstag."
    )
    long_chain = (
        f"Früh um halb sieben gestartet mit {v['w3']} danach {v['w4']} "
        f"zwischendurch {v['cust2']} leider {v['rain2']} "
        f"dementsprechend {v['plan']} {v['open_exp']}."
    )
    long_acts = v["a3"] + (v["a4"][:1] if v["a4"] else ())
    return [
        s(raw, v["a1"], problem=True, open_=True, customer=True, min_act=1),
        s(long_chain, long_acts, problem=True, open_=True, customer=True, min_act=1),
        s(f"Ja also vom Tag her {v['w2']} und also {v['w5']} und Feierabend.", v["a2"][:1] + v["a5"], min_act=1),
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

        start, step = 15, 5
    elif trade == "Tiefbau":
        def raw_at(q: int, i: int) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
            opts = (
                (f"Graben ziehen ca {q} Meter Rohre legen {q*4} Meter DN 125.", ("Graben ausgehoben", "Rohr"), ()),
                (f"{q} Meter Drainagerohr verlegt Noppenbahn verlegt Vlies.", ("Drainage",), ("Drainage", "Vlies")),
                (f"{q} LKW HT Bodenaushub {max(2, q // 2)} ton Bauschutt entsorgt Radlader {3 + i % 3} std.", (), ("LKW", "Bauschutt entsorgt")),
            )
            return opts[i % len(opts)]

        start, step = 11, 4
    else:
        def raw_at(q: int, i: int) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
            opts = (
                (f"{q} lfm Asphalt schneiden Merkstein setzen {max(1,q//10)} Stück.", ("Asphalt schneiden", "Merkstein"), ()),
                (f"{q} Quadratmeter asphaltieren {q+5} Meter TOK-Band LKW {2+i%4} std.", ("Asphalt eingebaut",), ("Asphalt", "TOK")),
                (f"{q} m2 Pflaster legen {q//2} ton Schotter Bagger {3+i%3} std.", ("Pflaster verlegt",), ("Schotter",)),
            )
            return opts[i % len(opts)]

        start, step = 14, 4
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
    items += _chains(v, trade)
    items += _explicit_p23(v, trade)
    items += _mega_and_long(v, trade)
    items += _broken_and_short(v, trade)
    need = TARGET_PER_TRADE - len(items)
    items += _qty_pad(v, trade, max(need, 1))
    return items[:TARGET_PER_TRADE]


def main() -> None:
    lines = [
        '"""Pilot-Welle 33 — PANZEK-Sphäre: 100 Basisszenarien pro Gewerk (generiert)."""',
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
